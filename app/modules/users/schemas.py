from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str
    organization_id: str


class UserUpdate(BaseModel):
    role: str | None = None


class UserDTO(BaseModel):
    id: str
    email: EmailStr
    role: str
    organization_id: str
    is_active: bool