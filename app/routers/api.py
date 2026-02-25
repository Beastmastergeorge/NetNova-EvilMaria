from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.models import Customer, Invoice, MonitoringEvent, RouterProvision
from app.schemas import (
    CustomerCreate,
    CustomerOut,
    CustomerUpdate,
    InvoiceCreate,
    InvoiceOut,
    InvoiceUpdate,
    MonitoringEventCreate,
    MonitoringEventOut,
    RouterProvisionOut,
)
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
        if customer.has_router:
            _ensure_router_provision(session, customer)
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

    @router.get("/customers/{customer_id}/router-config", response_model=RouterProvisionOut)
    def get_router_config(customer_id: int, session: Session = Depends(get_session)):
        customer = session.get(Customer, customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        if not customer.has_router:
            raise HTTPException(status_code=400, detail="Customer has no router enabled")
        return _ensure_router_provision(session, customer)

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
