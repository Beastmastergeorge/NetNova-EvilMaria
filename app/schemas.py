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


class InvoiceCreate(BaseModel):
    customer_id: int
    billing_month: str = Field(pattern=r"^\d{4}-\d{2}$")
    amount: float = Field(ge=0)


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
