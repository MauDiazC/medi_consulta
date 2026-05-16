from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class OrganizationCreate(BaseModel):
    name: str


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_period_end: Optional[datetime] = None


class OrganizationDTO(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    active: bool
    settings: Dict[str, Any] = {}
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    subscription_status: str = "trialing"
    subscription_period_end: Optional[datetime] = None