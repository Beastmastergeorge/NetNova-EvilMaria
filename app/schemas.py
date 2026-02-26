from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    plan_name: str = Field(min_length=2, max_length=80)
    monthly_rate: float = Field(ge=0)
    due_day: int = Field(ge=1, le=31)
    email: str = Field(min_length=5, max_length=255)
    has_router: bool = False
    router_identity: Optional[str] = Field(default=None, min_length=2, max_length=120)
    wan_interface: str = Field(default="ether1", min_length=2, max_length=40)
    lan_interface: str = Field(default="ether2", min_length=2, max_length=40)


class CustomerUpdate(BaseModel):
    plan_name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    monthly_rate: Optional[float] = Field(default=None, ge=0)
    due_day: Optional[int] = Field(default=None, ge=1, le=31)
    active: Optional[bool] = None


class CustomerOut(BaseModel):
    id: int
    name: str
    plan_name: str
    monthly_rate: float
    due_day: int
    email: str
    has_router: bool
    router_identity: Optional[str]
    wan_interface: str
    lan_interface: str
    active: bool
    created_at: datetime


class RouterProvisionOut(BaseModel):
    id: int
    customer_id: int
    subnet_cidr: str
    gateway_ip: str
    customer_ip: str
    script: str
    created_at: datetime


class InvoiceCreate(BaseModel):
    customer_id: int
    billing_month: str = Field(pattern=r"^\d{4}-\d{2}$")
    amount: float = Field(ge=0)


class InvoiceUpdate(BaseModel):
    status: str = Field(pattern=r"^(unpaid|paid|overdue)$")


class InvoiceOut(BaseModel):
    id: int
    customer_id: int
    billing_month: str
    amount: float
    status: str
    created_at: datetime
    paid_at: Optional[datetime]


class MonitoringEventCreate(BaseModel):
    service_name: str = Field(min_length=2, max_length=120)
    severity: str = Field(pattern=r"^(info|warning|critical)$")
    message: str = Field(min_length=2, max_length=500)


class MonitoringEventOut(BaseModel):
    id: int
    service_name: str
    severity: str
    message: str
    created_at: datetime
    acknowledged: bool
    acknowledged_at: Optional[datetime]
