from pydantic import BaseModel
from typing import Optional, Dict, Any


class OrganizationCreate(BaseModel):
    name: str


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class OrganizationDTO(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    active: bool
    settings: Dict[str, Any] = {}