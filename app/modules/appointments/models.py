import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), nullable=False)

    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(
        String(20), default="scheduled", nullable=False
    )  # scheduled, confirmed, cancelled, attended

    # Notification tracking
    reminder_immediate_sent = Column(Boolean, default=False)
    reminder_12h_sent = Column(Boolean, default=False)
    reminder_5m_sent = Column(Boolean, default=False)

    patient_confirmation = Column(Boolean, nullable=True)

    # Extra data (e.g. phone number if not in patient profile, AI context)
    metadata_json = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class AppointmentNotification(Base):
    __tablename__ = "appointment_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(String(30), nullable=False)  # welcome, reminder_12h, reminder_3h, reminder_15m
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        String(20), default="pending", nullable=False
    )  # pending, sent, delivered, read, failed
    error_message = Column(String, nullable=True)
    whatsapp_message_id = Column(String(100), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
