from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str
    organization_id: str


class UserUpdate(BaseModel):
    role: Optional[str] = None
    full_name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class UserDTO(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    organization_id: str
    active: bool
    settings: Dict[str, Any] = {}