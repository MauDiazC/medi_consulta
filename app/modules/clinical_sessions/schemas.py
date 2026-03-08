from pydantic import BaseModel


class ClinicalSessionCreate(BaseModel):
    patient_id: str


class ClinicalSessionDTO(BaseModel):
    id: str
    patient_id: str
    organization_id: str
    status: str