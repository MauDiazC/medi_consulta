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
    # Emergency Contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_address: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    emergency_contact_email: Optional[EmailStr] = None


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    birth_date: Optional[date] = None
    sex: Optional[str] = None
    # Emergency Contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_address: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    emergency_contact_email: Optional[EmailStr] = None


class PatientDTO(BaseModel):
    id: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    organization_id: str
    is_active: bool
    # Emergency Contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_address: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    emergency_contact_email: Optional[str] = None