from datetime import date

from pydantic import BaseModel, EmailStr


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    phone_number: str | None = None
    email: EmailStr | None = None
    birth_date: date | None = None
    sex: str | None = None  # M, F, O
    # Emergency Contact
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    emergency_contact_address: str | None = None
    emergency_contact_relationship: str | None = None
    emergency_contact_email: EmailStr | None = None


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    email: EmailStr | None = None
    birth_date: date | None = None
    sex: str | None = None
    # Emergency Contact
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    emergency_contact_address: str | None = None
    emergency_contact_relationship: str | None = None
    emergency_contact_email: EmailStr | None = None


class PatientDTO(BaseModel):
    id: str
    first_name: str
    last_name: str
    phone_number: str | None = None
    email: str | None = None
    organization_id: str
    is_active: bool
    # Emergency Contact
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    emergency_contact_address: str | None = None
    emergency_contact_relationship: str | None = None
    emergency_contact_email: str | None = None
