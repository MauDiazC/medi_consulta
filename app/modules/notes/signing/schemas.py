from pydantic import BaseModel
from typing import Optional


class ProfessionalIdentitySetup(BaseModel):
    public_key_pem: str
    license_number: str
    specialty: Optional[str] = None


class ProfessionalIdentityDTO(BaseModel):
    user_id: str
    organization_id: str
    public_key_pem: str
    license_number: str
    specialty: Optional[str] = None
    is_active: bool
