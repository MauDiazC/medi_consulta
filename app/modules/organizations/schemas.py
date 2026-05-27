from datetime import datetime
from typing import Any

from pydantic import BaseModel


class OrganizationCreate(BaseModel):
    name: str


class OrganizationUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    description: str | None = None
    logo_url: str | None = None
    settings: dict[str, Any] | None = None
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    subscription_status: str | None = None
    subscription_period_end: datetime | None = None


class OrganizationDTO(BaseModel):
    id: str
    name: str
    address: str | None = None
    phone: str | None = None
    description: str | None = None
    logo_url: str | None = None
    active: bool
    settings: dict[str, Any] = {}
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    subscription_status: str = "trialing"
    subscription_period_end: datetime | None = None
