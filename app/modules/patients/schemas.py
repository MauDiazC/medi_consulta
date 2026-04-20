from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    birth_date: Optional[date] = None
    sex: Optional[str] = None # M, F, O


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    birth_date: Optional[date] = None
    sex: Optional[str] = None


class PatientDTO(BaseModel):
    id: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    organization_id: str
    is_active: bool