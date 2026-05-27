from pydantic import BaseModel


class EncounterCreate(BaseModel):
    clinical_session_id: str
    patient_id: str
    doctor_id: str
    reason: str
    appointment_id: str | None = None


class EncounterUpdate(BaseModel):
    reason: str | None = None
