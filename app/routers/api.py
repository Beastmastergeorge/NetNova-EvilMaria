from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.models import Customer, Invoice, MonitoringEvent
from app.schemas import CustomerCreate, InvoiceCreate, MonitoringEventCreate, MonitoringEventOut
from app.services.metrics import collect_dashboard_metrics


def build_api_router(get_session) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["api"])

    @router.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/metrics")
    def metrics(session: Session = Depends(get_session)):
        return collect_dashboard_metrics(session)

    @router.post("/customers", status_code=201)
    def create_customer(payload: CustomerCreate, session: Session = Depends(get_session)):
        customer = Customer(**payload.model_dump())
        session.add(customer)
        session.commit()
        session.refresh(customer)
        return customer

    @router.post("/invoices", status_code=201)
    def create_invoice(payload: InvoiceCreate, session: Session = Depends(get_session)):
        customer = session.get(Customer, payload.customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        invoice = Invoice(**payload.model_dump())
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
