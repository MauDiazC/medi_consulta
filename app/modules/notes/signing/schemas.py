from pydantic import BaseModel


class ProfessionalIdentitySetup(BaseModel):
    public_key_pem: str
    license_number: str
    specialty: str | None = None


class ProfessionalIdentityDTO(BaseModel):
    user_id: str
    organization_id: str
    public_key_pem: str
    license_number: str
    specialty: str | None = None
    is_active: bool
