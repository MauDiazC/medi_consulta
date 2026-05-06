from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ClinicalSessionCreate(BaseModel):
    name: str


class ClinicalSessionUpdate(BaseModel):
    name: Optional[str] = None


class ClinicalSessionDTO(BaseModel):
    id: str
    name: str
    organization_id: str
    is_active: bool
    created_at: datetime
    closed_at: Optional[datetime] = None
    status: Optional[str] = "open"
