from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.models import (
    Customer,
    Invoice,
    MonitoringEvent,
    PaymentGateway,
    RouterProvision,
    Transaction,
    UserAccount,
)
from app.services.metrics import collect_dashboard_metrics
from app.services.mikrotik import assign_point_to_point_block, build_mikrotik_script


SESSION_COOKIE = "portal_user"


def _ensure_router_provision(session: Session, customer: Customer) -> RouterProvision:
    existing = session.exec(select(RouterProvision).where(RouterProvision.customer_id == customer.id)).first()
    if existing:
        return existing

    assignment = assign_point_to_point_block(customer.id)
    identity = customer.router_identity or f"NetNova-CPE-{customer.id}"
    script = build_mikrotik_script(
        customer_name=customer.name,
        router_identity=identity,
        wan_interface=customer.wan_interface,
        lan_interface=customer.lan_interface,
        gateway_ip=assignment.gateway_ip,
        customer_ip=assignment.customer_ip,
    )
    provision = RouterProvision(
        customer_id=customer.id,
        subnet_cidr=assignment.subnet_cidr,
        gateway_ip=assignment.gateway_ip,
        customer_ip=assignment.customer_ip,
        script=script,
    )
    session.add(provision)
    session.commit()
    session.refresh(provision)
    return provision


def _current_user(request: Request, session: Session) -> UserAccount | None:
    username = request.cookies.get(SESSION_COOKIE)
    if not username:
        return None
    return session.exec(select(UserAccount).where(UserAccount.username == username, UserAccount.active.is_(True))).first()


def _ensure_admin(request: Request, session: Session) -> UserAccount:
    user = _current_user(request, session)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def _ensure_client(request: Request, session: Session) -> tuple[UserAccount, Customer]:
    user = _current_user(request, session)
    if not user or user.role != "client" or not user.customer_id:
        raise HTTPException(status_code=403, detail="Client access required")
    customer = session.get(Customer, user.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return user, customer


def _bootstrap_admin(session: Session) -> None:
    admin = session.exec(select(UserAccount).where(UserAccount.role == "admin")).first()
    if admin:
        return
    seed = UserAccount(username="admin", password="admin123", role="admin", active=True)
    session.add(seed)
    session.commit()


def build_web_router(get_session, templates: Jinja2Templates) -> APIRouter:
    router = APIRouter()

    @router.get("/", response_class=HTMLResponse)
    def root(request: Request, session: Session = Depends(get_session)):
        _bootstrap_admin(session)
        user = _current_user(request, session)
        if not user:
            return RedirectResponse(url="/login", status_code=303)
        if user.role == "admin":
            return RedirectResponse(url="/admin/dashboard", status_code=303)
        return RedirectResponse(url="/client/portal", status_code=303)

    @router.get("/login", response_class=HTMLResponse)
    def login_page(request: Request, session: Session = Depends(get_session)):
        _bootstrap_admin(session)
        return templates.TemplateResponse("login.html", {"request": request, "error": ""})

    @router.post("/login")
    def login(
        username: str = Form(...),
        password: str = Form(...),
        session: Session = Depends(get_session),
    ):
        _bootstrap_admin(session)
        account = session.exec(select(UserAccount).where(UserAccount.username == username, UserAccount.active.is_(True))).first()
        if not account or account.password != password:
            return RedirectResponse(url="/login?error=invalid", status_code=303)

        redirect_to = "/admin/dashboard" if account.role == "admin" else "/client/portal"
        response = RedirectResponse(url=redirect_to, status_code=303)
        response.set_cookie(SESSION_COOKIE, account.username, httponly=True, samesite="lax")
        return response

    @router.post("/logout")
    def logout():
        response = RedirectResponse(url="/login", status_code=303)
        response.delete_cookie(SESSION_COOKIE)
        return response

    @router.get("/admin/dashboard", response_class=HTMLResponse)
    def admin_dashboard(request: Request, session: Session = Depends(get_session)):
        admin = _ensure_admin(request, session)
        customers = session.exec(select(Customer).order_by(Customer.created_at.desc())).all()
        accounts = session.exec(select(UserAccount).where(UserAccount.role == "client").order_by(UserAccount.created_at.desc())).all()
        invoices = session.exec(select(Invoice).order_by(Invoice.created_at.desc())).all()
        events = session.exec(select(MonitoringEvent).order_by(MonitoringEvent.created_at.desc())).all()
        router_configs = session.exec(select(RouterProvision).order_by(RouterProvision.created_at.desc())).all()
        return templates.TemplateResponse(
            "admin_dashboard.html",
            {
                "request": request,
                "admin": admin,
                "customers": customers,
                "accounts": accounts,
                "invoices": invoices,
                "events": events,
                "router_configs": router_configs,
                "stats": collect_dashboard_metrics(session),
            },
        )

    @router.post("/admin/accounts")
    def create_client_account(
        name: str = Form(...),
        email: str = Form(...),
        username: str = Form(...),
        password: str = Form(...),
        plan_name: str = Form(...),
        monthly_rate: float = Form(...),
        due_day: int = Form(...),
        has_router: bool = Form(False),
        router_identity: str = Form(""),
        wan_interface: str = Form("ether1"),
        lan_interface: str = Form("ether2"),
        session: Session = Depends(get_session),
        request: Request = None,
    ):
        _ensure_admin(request, session)
        existing = session.exec(select(UserAccount).where(UserAccount.username == username)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")

        customer = Customer(
            name=name,
            plan_name=plan_name,
            monthly_rate=monthly_rate,
            due_day=due_day,
            email=email,
            has_router=has_router,
            router_identity=router_identity or None,
            wan_interface=wan_interface,
            lan_interface=lan_interface,
        )
        session.add(customer)
        session.commit()
        session.refresh(customer)

        account = UserAccount(username=username, password=password, role="client", customer_id=customer.id)
        session.add(account)
        if has_router:
            _ensure_router_provision(session, customer)
        session.commit()
        return RedirectResponse(url="/admin/dashboard", status_code=303)

    @router.post("/admin/accounts/{account_id}/toggle")
    def toggle_client_account(account_id: int, request: Request, session: Session = Depends(get_session)):
        _ensure_admin(request, session)
        account = session.get(UserAccount, account_id)
        if not account or account.role != "client":
            raise HTTPException(status_code=404, detail="Client account not found")
        account.active = not account.active
        session.add(account)
        session.commit()
        return RedirectResponse(url="/admin/dashboard", status_code=303)

    @router.post("/admin/accounts/{account_id}/remove")
    def remove_client_account(account_id: int, request: Request, session: Session = Depends(get_session)):
        _ensure_admin(request, session)
        account = session.get(UserAccount, account_id)
        if not account or account.role != "client":
            raise HTTPException(status_code=404, detail="Client account not found")
        session.delete(account)
        session.commit()
        return RedirectResponse(url="/admin/dashboard", status_code=303)

    @router.get("/client/portal", response_class=HTMLResponse)
    def client_portal(request: Request, session: Session = Depends(get_session)):
        user, customer = _ensure_client(request, session)
        invoices = session.exec(select(Invoice).where(Invoice.customer_id == customer.id).order_by(Invoice.created_at.desc())).all()
        transactions = session.exec(
            select(Transaction).where(Transaction.customer_id == customer.id).order_by(Transaction.created_at.desc())
        ).all()
        gateways = session.exec(
            select(PaymentGateway).where(PaymentGateway.customer_id == customer.id).order_by(PaymentGateway.created_at.desc())
        ).all()
        router = session.exec(select(RouterProvision).where(RouterProvision.customer_id == customer.id)).first()
        return templates.TemplateResponse(
            "client_portal.html",
            {
                "request": request,
                "user": user,
                "customer": customer,
                "invoices": invoices,
                "transactions": transactions,
                "gateways": gateways,
                "router": router,
            },
        )

    @router.post("/client/profile")
    def update_client_profile(
        request: Request,
        plan_name: str = Form(...),
        monthly_rate: float = Form(...),
        due_day: int = Form(...),
        email: str = Form(...),
        session: Session = Depends(get_session),
    ):
        _, customer = _ensure_client(request, session)
        customer.plan_name = plan_name
        customer.monthly_rate = monthly_rate
        customer.due_day = due_day
        customer.email = email
        session.add(customer)
        session.commit()
        return RedirectResponse(url="/client/portal", status_code=303)

    @router.post("/client/payment-gateways")
    def add_payment_gateway(
        request: Request,
        gateway_name: str = Form(...),
        account_ref: str = Form(...),
        session: Session = Depends(get_session),
    ):
        _, customer = _ensure_client(request, session)
        gateway = PaymentGateway(customer_id=customer.id, gateway_name=gateway_name, account_ref=account_ref)
        session.add(gateway)
        session.commit()
        return RedirectResponse(url="/client/portal", status_code=303)

    @router.post("/client/routers")
    def update_router(
        request: Request,
        router_identity: str = Form(...),
        wan_interface: str = Form("ether1"),
        lan_interface: str = Form("ether2"),
        session: Session = Depends(get_session),
    ):
        _, customer = _ensure_client(request, session)
        customer.has_router = True
        customer.router_identity = router_identity
        customer.wan_interface = wan_interface
        customer.lan_interface = lan_interface
        session.add(customer)
        session.commit()
        _ensure_router_provision(session, customer)
        return RedirectResponse(url="/client/portal", status_code=303)

    @router.get("/client/router-script", response_class=PlainTextResponse)
    def client_router_script(request: Request, session: Session = Depends(get_session)):
        _, customer = _ensure_client(request, session)
        if not customer.has_router:
            raise HTTPException(status_code=400, detail="Router not configured")
        provision = _ensure_router_provision(session, customer)
        return provision.script

    @router.post("/client/transactions")
    def add_transaction(
        request: Request,
        amount: float = Form(...),
        method: str = Form(...),
        reference: str = Form(...),
        session: Session = Depends(get_session),
    ):
        _, customer = _ensure_client(request, session)
        tx = Transaction(customer_id=customer.id, amount=amount, method=method, reference=reference)
        session.add(tx)
        session.commit()
        return RedirectResponse(url="/client/portal", status_code=303)

    @router.get("/customers/{customer_id}/router-config", response_class=PlainTextResponse)
    def download_router_config(customer_id: int, session: Session = Depends(get_session)):
        customer = session.get(Customer, customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        if not customer.has_router:
            raise HTTPException(status_code=400, detail="Customer has no router enabled")

        provision = _ensure_router_provision(session, customer)
        return provision.script

    @router.post("/events/{event_id}/ack")
    def ack_event(event_id: int, request: Request, session: Session = Depends(get_session)):
        _ensure_admin(request, session)
        event = session.get(MonitoringEvent, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        event.acknowledged = True
        event.acknowledged_at = datetime.utcnow()
        session.add(event)
        session.commit()
        return RedirectResponse(url="/admin/dashboard", status_code=303)

    return router
