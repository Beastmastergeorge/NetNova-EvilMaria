from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(min_length=2, max_length=120, index=True)
    plan_name: str = Field(min_length=2, max_length=80)
    monthly_rate: float = Field(ge=0)
    due_day: int = Field(ge=1, le=31)
    email: str = Field(min_length=5, max_length=255, index=True)
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Invoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id", index=True)
    billing_month: str = Field(regex=r"^\d{4}-\d{2}$")
    amount: float = Field(ge=0)
    status: str = Field(default="unpaid", regex=r"^(unpaid|paid|overdue)$")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = None


class MonitoringEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    service_name: str = Field(min_length=2, max_length=120, index=True)
    severity: str = Field(regex=r"^(info|warning|critical)$")
    message: str = Field(min_length=2, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    acknowledged: bool = Field(default=False, index=True)
    acknowledged_at: Optional[datetime] = None
