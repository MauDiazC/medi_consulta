import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import JSON, Column, DateTime, String, Boolean, event
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class StructuralIntegrityError(Exception):
    """Raised when a structural retention or immutability rule is violated."""
    pass

class ImmutableLegalArtifact:
    """
    Mixin for institutional-grade record preservation.
    Enforced structurally via SQLAlchemy event listeners.
    """
    retention_until = Column(DateTime(timezone=True), nullable=True, index=True)
    archival_status = Column(String(20), default="active", nullable=False)
    legal_hold = Column(Boolean, default=False, nullable=False)
    is_immutable = Column(Boolean, default=False, nullable=False)
    retention_source = Column(String(100), nullable=True) # e.g., "NOM-004-SSA3-2012"

    def validate_modification_safety(self):
        if self.is_immutable:
            raise StructuralIntegrityError(f"Structural Violation: Entity {self.__class__.__name__} is immutable.")
        if self.legal_hold:
            raise StructuralIntegrityError(f"Structural Violation: Entity {self.__class__.__name__} is under Legal Hold.")
        if self.retention_until and datetime.now(timezone.utc) < self.retention_until:
            raise StructuralIntegrityError(f"Structural Violation: Retention has not expired for {self.__class__.__name__}.")

# --- Infrastructure Enforcement Layers ---

@event.listens_for(ImmutableLegalArtifact, "before_update", propagate=True)
def block_immutable_updates(mapper, connection, target):
    target.validate_modification_safety()

@event.listens_for(ImmutableLegalArtifact, "before_delete", propagate=True)
def block_all_physical_deletes(mapper, connection, target):
    raise StructuralIntegrityError(f"Structural Violation: Physical deletion prohibited for {target.__class__.__name__}.")

@event.listens_for(Session, "before_flush")
def session_integrity_guard(session, flush_context, instances):
    """
    Session-level interceptor to prevent bulk or indirect mutation paths.
    """
    for obj in session.dirty:
        if isinstance(obj, ImmutableLegalArtifact):
            obj.validate_modification_safety()
    
    for obj in session.deleted:
        if isinstance(obj, ImmutableLegalArtifact):
            raise StructuralIntegrityError(f"Structural Violation: Deletion intercepted at session level for {obj.__class__.__name__}.")

# --- Infrastructure Models ---

class OutboxEvent(Base, ImmutableLegalArtifact):
    __tablename__ = "outbox_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    processed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime(timezone=True), nullable=True)

class IdempotencyKey(Base, ImmutableLegalArtifact):
    __tablename__ = "idempotency_keys"
    id = Column(String(255), primary_key=True)
    response_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ClinicalAuditLog(Base, ImmutableLegalArtifact):
    __tablename__ = "clinical_audit_log"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity = Column(String, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String, nullable=False)
    performed_by = Column(UUID(as_uuid=True), nullable=True)
    entry_metadata = Column(JSON, nullable=True) # Renamed from metadata
    previous_hash = Column(String(128), nullable=True)
    entry_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
