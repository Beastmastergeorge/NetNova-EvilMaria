from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.models import Customer, Invoice, MonitoringEvent
from app.services.metrics import collect_dashboard_metrics


def build_web_router(get_session, templates: Jinja2Templates) -> APIRouter:
    router = APIRouter()

    @router.get("/", response_class=HTMLResponse)
    def dashboard(request: Request, session: Session = Depends(get_session)):
        customers = session.exec(select(Customer).order_by(Customer.created_at.desc())).all()
        invoices = session.exec(select(Invoice).order_by(Invoice.created_at.desc())).all()
        events = session.exec(select(MonitoringEvent).order_by(MonitoringEvent.created_at.desc())).all()

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "customers": customers,
                "invoices": invoices,
                "events": events,
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
        session: Session = Depends(get_session),
    ):
        customer = Customer(
            name=name,
            plan_name=plan_name,
            monthly_rate=monthly_rate,
            due_day=due_day,
            email=email,
        )
        session.add(customer)
        session.commit()
        return RedirectResponse(url="/", status_code=303)

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
