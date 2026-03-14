from pydantic import BaseModel


class ClinicalSessionCreate(BaseModel):
    name: str


class ClinicalSessionDTO(BaseModel):
    id: str
    name: str
    organization_id: str
    status: str | None = None