from pydantic import BaseModel


class EncounterCreate(BaseModel):
    clinical_session_id: str
    patient_id: str
    reason: str


class EncounterUpdate(BaseModel):
    reason: str | None = None