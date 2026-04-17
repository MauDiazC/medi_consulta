from pydantic import BaseModel
from typing import Optional


class ClinicalSessionCreate(BaseModel):
    name: str


class ClinicalSessionUpdate(BaseModel):
    name: Optional[str] = None


class ClinicalSessionDTO(BaseModel):
    id: str
    name: str
    organization_id: str
    is_active: bool
    status: Optional[str] = "open"