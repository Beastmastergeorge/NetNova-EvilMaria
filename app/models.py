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
    has_router: bool = Field(default=False, index=True)
    router_identity: Optional[str] = Field(default=None, max_length=120)
    wan_interface: str = Field(default="ether1", max_length=40)
    lan_interface: str = Field(default="ether2", max_length=40)
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserAccount(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=80)
    password: str = Field(max_length=255)
    role: str = Field(default="client", regex=r"^(admin|client)$")
    customer_id: Optional[int] = Field(default=None, foreign_key="customer.id", unique=True)
    active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RouterProvision(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id", unique=True, index=True)
    subnet_cidr: str = Field(max_length=32)
    gateway_ip: str = Field(max_length=40)
    customer_ip: str = Field(max_length=40)
    script: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PaymentGateway(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id", index=True)
    gateway_name: str = Field(max_length=80)
    account_ref: str = Field(max_length=120)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id", index=True)
    amount: float = Field(ge=0)
    method: str = Field(max_length=80)
    reference: str = Field(max_length=120)
    status: str = Field(default="completed", regex=r"^(completed|failed|pending)$")
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
