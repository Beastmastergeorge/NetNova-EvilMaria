from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.models import Customer, Invoice, MonitoringEvent
from app.schemas import (
    CustomerCreate,
    CustomerOut,
    CustomerUpdate,
    InvoiceCreate,
    InvoiceOut,
    InvoiceUpdate,
    MonitoringEventCreate,
    MonitoringEventOut,
)
from app.services.metrics import collect_dashboard_metrics


def build_api_router(get_session) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["api"])

    @router.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/metrics")
    def metrics(session: Session = Depends(get_session)):
        return collect_dashboard_metrics(session)

    @router.get("/customers", response_model=list[CustomerOut])
    def list_customers(session: Session = Depends(get_session)):
        return session.exec(select(Customer).order_by(Customer.created_at.desc())).all()

    @router.post("/customers", response_model=CustomerOut, status_code=201)
    def create_customer(payload: CustomerCreate, session: Session = Depends(get_session)):
        customer = Customer(**payload.model_dump())
        session.add(customer)
        session.commit()
        session.refresh(customer)
        return customer

    @router.patch("/customers/{customer_id}", response_model=CustomerOut)
    def update_customer(customer_id: int, payload: CustomerUpdate, session: Session = Depends(get_session)):
        customer = session.get(Customer, customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        for key, value in payload.model_dump(exclude_none=True).items():
            setattr(customer, key, value)
        session.add(customer)
        session.commit()
        session.refresh(customer)
        return customer

    @router.get("/invoices", response_model=list[InvoiceOut])
    def list_invoices(status: str | None = None, session: Session = Depends(get_session)):
        statement = select(Invoice).order_by(Invoice.created_at.desc())
        if status:
            statement = statement.where(Invoice.status == status)
        return session.exec(statement).all()

    @router.post("/invoices", response_model=InvoiceOut, status_code=201)
    def create_invoice(payload: InvoiceCreate, session: Session = Depends(get_session)):
        customer = session.get(Customer, payload.customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        invoice = Invoice(**payload.model_dump())
        session.add(invoice)
        session.commit()
        session.refresh(invoice)
        return invoice

    @router.patch("/invoices/{invoice_id}", response_model=InvoiceOut)
    def update_invoice(invoice_id: int, payload: InvoiceUpdate, session: Session = Depends(get_session)):
        invoice = session.get(Invoice, invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        invoice.status = payload.status
        invoice.paid_at = datetime.utcnow() if payload.status == "paid" else None
        session.add(invoice)
        session.commit()
        session.refresh(invoice)
        return invoice

    @router.post("/events", response_model=MonitoringEventOut, status_code=201)
    def create_event(payload: MonitoringEventCreate, session: Session = Depends(get_session)):
        event = MonitoringEvent(**payload.model_dump())
        session.add(event)
        session.commit()
        session.refresh(event)
        return event

    @router.get("/events", response_model=list[MonitoringEventOut])
    def list_events(unacknowledged_only: bool = False, session: Session = Depends(get_session)):
        statement = select(MonitoringEvent).order_by(MonitoringEvent.created_at.desc())
        if unacknowledged_only:
            statement = statement.where(MonitoringEvent.acknowledged.is_(False))
        return session.exec(statement).all()

    @router.post("/events/{event_id}/ack", response_model=MonitoringEventOut)
    def ack_event(event_id: int, session: Session = Depends(get_session)):
        event = session.get(MonitoringEvent, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        event.acknowledged = True
        event.acknowledged_at = datetime.utcnow()
        session.add(event)
        session.commit()
        session.refresh(event)
        return event

    return router
