import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Triage(Base):
    __tablename__ = "triage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    appointment_id = Column(UUID(as_uuid=True), nullable=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), nullable=False)

    # Vital Signs
    heart_rate = Column(Float, nullable=True) # Frecuencia cardiaca
    oxygen_saturation = Column(Float, nullable=True) # Saturación de oxigeno
    blood_pressure = Column(String(20), nullable=True) # Presión arterial (e.g. 120/80)
    weight = Column(Float, nullable=True) # Peso
    height = Column(Float, nullable=True) # Talla
    temperature = Column(Float, nullable=True) # Temperatura

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
