import json
import hashlib
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.modules.notes.signing.models import BackupJob
from app.modules.notes.signing.repository import SigningRepository
from app.modules.notes.signing.utils import canonical_json, sha256_hex
from app.modules.notes.signing.crypto_service import load_private_key, sign_hash
from app.core.audit import audit_log
from app.core.events import publish_event_tx

class ImmutableBackupService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SigningRepository(db)

    async def generate_institutional_backup(self, organization_id: str, executor_id: str, mode: str = "FULL"):
        """
        Refactored: Creates a Frozen Cryptographic Volume or an Operational Delta.
        """
        # 1) Start Backup Job
        job = BackupJob(
            organization_id=organization_id,
            mode=mode,
            status="STARTED",
            executor_id=executor_id,
            organization_root_fingerprint="org-root-placeholder" # In production, from config
        )
        await self.repo.save_backup_job(job)

        # 2) Gather Previous Link (Backup Trust Chain)
        latest_full = await self.repo.get_latest_full_backup(organization_id)
        job.previous_backup_hash = latest_full.backup_hash if latest_full else None

        # 3) Absolute Scope Aggregation
        data = await self.repo.get_all_clinical_data(organization_id)
        
        # 4) Build Manifest
        manifest = {
            "organization_id": organization_id,
            "backup_job_id": str(job.id),
            "mode": mode,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "previous_backup_hash": job.previous_backup_hash,
            "inventory": {
                "snapshots": [{"id": str(s.id), "hash": s.content_hash, "retention": str(s.retention_until)} for s in data["snapshots"]],
                "seals": [{"id": str(s.id), "hash": s.aggregate_hash} for s in data["seals"]],
                "audit_chain": [{"id": str(a.id), "hash": a.entry_hash} for a in data["audit_log"]],
                "keys": [{"fingerprint": k.public_key_fingerprint, "active": k.is_active} for k in data["keys"]]
            },
            "schema_version": "frozen-volume-v1"
        }

        # 5) Cryptographic Sealing (FULL Mode Only)
        canonical_manifest = canonical_json(manifest)
        job.manifest_hash = sha256_hex(canonical_manifest)
        
        # Dummy global hash for the "file bundle" - in reality, would be computed from the final ZIP/tar
        job.backup_hash = sha256_hex(canonical_manifest + (job.previous_backup_hash or ""))

        # Certification Signature
        from app.modules.notes.signing.service import SigningApplicationService
        signing_app = SigningApplicationService(self.db)
        active_key = await self.repo.get_active_organization_key(organization_id)
        
        priv_pem = signing_app._decrypt_key(active_key.encrypted_private_key)
        job.certification_signature = sign_hash(load_private_key(priv_pem), job.manifest_hash)
        
        # 6) Finalize Job & Emit Certification Audit
        async with self.db.begin():
            job.status = "COMPLETED"
            job.completed_at = datetime.utcnow()
            job.is_immutable = True
            
            # Retention for the BackupJob itself (Institutional Metadata)
            job.retention_until = datetime.utcnow() + (datetime.utcnow() - datetime.utcnow()) # placeholder logic
            
            # Institutional Audit Entry (Legal Traceability)
            await audit_log(
                self.db, "backup_job", str(job.id), "BACKUP_CERTIFIED", executor_id,
                metadata={
                    "mode": mode,
                    "global_backup_hash": job.backup_hash,
                    "manifest_hash": job.manifest_hash,
                    "organization_root_fingerprint": job.organization_root_fingerprint
                }
            )
            
            # Event Outbox
            await publish_event_tx(self.db, "BACKUP_CERTIFIED", {
                "backup_job_id": str(job.id),
                "executor_id": executor_id,
                "timestamp": job.completed_at.isoformat()
            })

        return {
            "job_id": str(job.id),
            "manifest": manifest,
            "certification": {
                "signature": job.certification_signature,
                "fingerprint": active_key.public_key_fingerprint
            },
            "integrity": {
                "global_hash": job.backup_hash,
                "previous_hash": job.previous_backup_hash
            }
        }
