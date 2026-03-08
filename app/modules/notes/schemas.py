from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ClinicalNoteBase(BaseModel):
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None


class ClinicalNoteCreate(ClinicalNoteBase):
    encounter_id: UUID
    created_by: UUID


class ClinicalNoteUpdate(ClinicalNoteBase):
    pass


class ClinicalNoteResponse(ClinicalNoteBase):
    id: UUID
    encounter_id: UUID
    version: int
    created_by: UUID
    signed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class AIDraftRequest(BaseModel):
    encounter_id: UUID
    patient_id: UUID
    prompt: str