from datetime import datetime

from pydantic import BaseModel


class ClinicalSessionCreate(BaseModel):
    name: str


class ClinicalSessionUpdate(BaseModel):
    name: str | None = None


class ClinicalSessionDTO(BaseModel):
    id: str
    name: str
    organization_id: str
    is_active: bool
    created_at: datetime
    closed_at: datetime | None = None
    status: str | None = "open"
