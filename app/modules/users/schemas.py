from typing import Any

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str
    organization_id: str


class UserUpdate(BaseModel):
    role: str | None = None
    full_name: str | None = None
    settings: dict[str, Any] | None = None
    slug: str | None = None


class UserDTO(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    organization_id: str
    active: bool
    settings: dict[str, Any] = {}
    slug: str | None = None
