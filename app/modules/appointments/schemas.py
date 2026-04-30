from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

class AppointmentBase(BaseModel):
    patient_id: UUID
    doctor_id: UUID
    scheduled_at: datetime
    metadata_json: dict | None = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    status: str | None = None
    patient_confirmation: bool | None = None

class AppointmentRead(AppointmentBase):
    id: UUID
    status: str
    patient_confirmation: bool | None
    created_at: datetime
    updated_at: datetime
    
    # Extended fields for UI
    patient_first_name: str | None = None
    patient_last_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
