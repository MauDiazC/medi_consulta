import uuid
from datetime import datetime

from sqlalchemy import (JSON, Column, DateTime, ForeignKey, String, Boolean,
                        UniqueConstraint)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.core.models import ImmutableLegalArtifact


class NoteSnapshot(Base, ImmutableLegalArtifact):
    __tablename__ = "note_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    note_id = Column(UUID(as_uuid=True), ForeignKey("notes.id"), nullable=False)
    version_id = Column(UUID(as_uuid=True), nullable=False)
    snapshot_json = Column(JSON, nullable=False)
    content_hash = Column(String(128), nullable=False)
    signature = Column(String, nullable=False)
    signed_by = Column(UUID(as_uuid=True), nullable=False)
    signed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    public_key_fingerprint = Column(String(128), nullable=False)
    previous_snapshot_hash = Column(String(128), nullable=True, index=True)
    pdf_path = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("version_id", name="uq_snapshot_version"),
    )


class EncounterSeal(Base, ImmutableLegalArtifact):
    __tablename__ = "encounter_seals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    aggregate_hash = Column(String(128), nullable=False)
    signature = Column(String, nullable=False)
    signed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    public_key_fingerprint = Column(String(128), nullable=False)
    seal_payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class OrganizationKey(Base, ImmutableLegalArtifact):
    __tablename__ = "organization_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    public_key_pem = Column(String, nullable=False)
    public_key_fingerprint = Column(String(128), nullable=False, unique=True)
    encrypted_private_key = Column(String, nullable=False)  # AES-GCM Encrypted PEM
    organization_root_fingerprint = Column(String(128), nullable=True) # Immutable anchor
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    retired_at = Column(DateTime, nullable=True)

    __table_args__ = (
        # Ensure only one active key per organization (requires partial index in Postgres, 
        # but we'll enforce logically in service for now)
    )


class BackupJob(Base, ImmutableLegalArtifact):
    __tablename__ = "backup_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    mode = Column(String(20), nullable=False) # FULL, INCREMENTAL
    status = Column(String(20), nullable=False) # STARTED, COMPLETED, FAILED
    
    # Cryptographic Anchors
    backup_hash = Column(String(128), nullable=True) # Global bundle hash
    manifest_hash = Column(String(128), nullable=True) # manifest.json hash
    certification_signature = Column(String, nullable=True) # Signed manifest_hash
    organization_root_fingerprint = Column(String(128), nullable=False)
    
    # Backup Trust Chain
    previous_backup_hash = Column(String(128), nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    executor_id = Column(UUID(as_uuid=True), nullable=False)

    __table_args__ = (
        # Enforce institutional preservation
    )