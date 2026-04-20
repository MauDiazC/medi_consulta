import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), nullable=False)
    
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(20), default="scheduled", nullable=False) # scheduled, confirmed, cancelled, attended
    
    # Notification tracking
    reminder_immediate_sent = Column(Boolean, default=False)
    reminder_12h_sent = Column(Boolean, default=False)
    reminder_5m_sent = Column(Boolean, default=False)
    
    patient_confirmation = Column(Boolean, nullable=True)
    
    # Extra data (e.g. phone number if not in patient profile, AI context)
    metadata_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
