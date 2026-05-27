from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
    is_triage: bool = False

    model_config = ConfigDict(from_attributes=True)


class SlotRead(BaseModel):
    start_time: str
    end_time: str
    status: str  # "free" or "occupied"
    appointment_id: UUID | None = None


class AppointmentNotificationRead(BaseModel):
    id: UUID
    appointment_id: UUID
    type: str
    sent_at: datetime | None = None
    status: str
    error_message: str | None = None
    whatsapp_message_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
