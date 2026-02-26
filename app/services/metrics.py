from __future__ import annotations

from sqlmodel import Session, select

from app.models import Customer, Invoice, MonitoringEvent


def collect_dashboard_metrics(session: Session) -> dict[str, float | int]:
    customers = session.exec(select(Customer)).all()
    invoices = session.exec(select(Invoice)).all()
    events = session.exec(select(MonitoringEvent)).all()

    return {
        "customer_count": len(customers),
        "mrr": round(sum(customer.monthly_rate for customer in customers), 2),
        "unpaid": round(sum(invoice.amount for invoice in invoices if invoice.status != "paid"), 2),
        "critical_count": sum(1 for event in events if event.severity == "critical" and not event.acknowledged),
    }
