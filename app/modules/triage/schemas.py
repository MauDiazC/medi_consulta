from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class TriageBase(BaseModel):
    patient_id: UUID
    appointment_id: Optional[UUID] = None
    heart_rate: Optional[float] = None
    oxygen_saturation: Optional[float] = None
    blood_pressure: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    temperature: Optional[float] = None

class TriageCreate(TriageBase):
    pass

class TriageRead(TriageBase):
    id: UUID
    doctor_id: UUID
    organization_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
