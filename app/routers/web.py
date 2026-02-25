from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.models import Customer, Invoice, MonitoringEvent, RouterProvision
from app.services.metrics import collect_dashboard_metrics
from app.services.mikrotik import assign_point_to_point_block, build_mikrotik_script


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


def build_web_router(get_session, templates: Jinja2Templates) -> APIRouter:
    router = APIRouter()

    @router.get("/", response_class=HTMLResponse)
    def dashboard(request: Request, session: Session = Depends(get_session)):
        customers = session.exec(select(Customer).order_by(Customer.created_at.desc())).all()
        invoices = session.exec(select(Invoice).order_by(Invoice.created_at.desc())).all()
        events = session.exec(select(MonitoringEvent).order_by(MonitoringEvent.created_at.desc())).all()
        router_configs = session.exec(select(RouterProvision).order_by(RouterProvision.created_at.desc())).all()

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "customers": customers,
                "invoices": invoices,
                "events": events,
                "router_configs": router_configs,
                "stats": collect_dashboard_metrics(session),
            },
        )

    @router.post("/customers")
    def add_customer(
        name: str = Form(...),
        plan_name: str = Form(...),
        monthly_rate: float = Form(...),
        due_day: int = Form(...),
        email: str = Form(...),
        has_router: bool = Form(False),
        router_identity: str = Form(""),
        wan_interface: str = Form("ether1"),
        lan_interface: str = Form("ether2"),
        session: Session = Depends(get_session),
    ):
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

        if customer.has_router:
            _ensure_router_provision(session, customer)

        return RedirectResponse(url="/", status_code=303)

    @router.get("/customers/{customer_id}/router-config", response_class=PlainTextResponse)
    def download_router_config(customer_id: int, session: Session = Depends(get_session)):
        customer = session.get(Customer, customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        if not customer.has_router:
            raise HTTPException(status_code=400, detail="Customer has no router enabled")

        provision = _ensure_router_provision(session, customer)
        return provision.script

    @router.post("/customers/{customer_id}/toggle")
    def toggle_customer_status(customer_id: int, session: Session = Depends(get_session)):
        customer = session.get(Customer, customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        customer.active = not customer.active
        session.add(customer)
        session.commit()
        return RedirectResponse(url="/", status_code=303)

    @router.post("/invoices")
    def create_invoice(
        customer_id: int = Form(...),
        billing_month: str = Form(...),
        amount: float = Form(...),
        session: Session = Depends(get_session),
    ):
        customer = session.get(Customer, customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        invoice = Invoice(customer_id=customer_id, billing_month=billing_month, amount=amount)
        session.add(invoice)
        session.commit()
        return RedirectResponse(url="/", status_code=303)

    @router.post("/invoices/{invoice_id}/mark-paid")
    def mark_invoice_paid(invoice_id: int, session: Session = Depends(get_session)):
        invoice = session.get(Invoice, invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        invoice.status = "paid"
        invoice.paid_at = datetime.utcnow()
        session.add(invoice)
        session.commit()
        return RedirectResponse(url="/", status_code=303)

    @router.post("/events")
    def create_event(
        service_name: str = Form(...),
        severity: str = Form(...),
        message: str = Form(...),
        session: Session = Depends(get_session),
    ):
        event = MonitoringEvent(service_name=service_name, severity=severity, message=message)
        session.add(event)
        session.commit()
        return RedirectResponse(url="/", status_code=303)

    @router.post("/events/{event_id}/ack")
    def ack_event(event_id: int, session: Session = Depends(get_session)):
        event = session.get(MonitoringEvent, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        event.acknowledged = True
        event.acknowledged_at = datetime.utcnow()
        session.add(event)
        session.commit()
        return RedirectResponse(url="/", status_code=303)

    return router
