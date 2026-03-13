from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, text, update
from app.modules.notes.signing.models import NoteSnapshot, EncounterSeal, OrganizationKey, BackupJob
from app.core.models import OutboxEvent, IdempotencyKey, ClinicalAuditLog

class SigningRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_snapshot(self, snapshot: NoteSnapshot):
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot

    async def get_by_note_id(self, note_id: str):
        stmt = select(NoteSnapshot).where(NoteSnapshot.note_id == note_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_latest_snapshot_for_encounter(self, encounter_id: str):
        """
        Traverses back in the longitudinal record using raw SQL join.
        """
        stmt = text("""
            SELECT ns.id
            FROM note_snapshots ns
            JOIN clinical_notes cn ON ns.note_id = cn.id
            WHERE cn.encounter_id = :eid
            ORDER BY ns.signed_at DESC
            LIMIT 1
        """)
        result = await self.db.execute(stmt, {"eid": encounter_id})
        snapshot_id = result.scalar()
        if not snapshot_id:
            return None
        return await self.db.get(NoteSnapshot, snapshot_id)

    async def get_all_snapshots_for_encounter(self, encounter_id: str):
        """
        Retrieves all signed snapshots for an encounter using raw SQL join.
        """
        stmt = text("""
            SELECT ns.id
            FROM note_snapshots ns
            JOIN clinical_notes cn ON ns.note_id = cn.id
            WHERE cn.encounter_id = :eid
            ORDER BY ns.signed_at ASC
        """)
        result = await self.db.execute(stmt, {"eid": encounter_id})
        ids = result.scalars().all()
        
        snapshots = []
        for sid in ids:
            sn = await self.db.get(NoteSnapshot, sid)
            if sn: snapshots.append(sn)
        return snapshots

    async def has_unsigned_notes(self, encounter_id: str):
        stmt = text("""
            SELECT count(*) 
            FROM clinical_notes 
            WHERE encounter_id = :eid 
            AND signed_at IS NULL
        """)
        result = await self.db.execute(stmt, {"eid": encounter_id})
        count = result.scalar()
        return count > 0

    async def has_active_locks(self, encounter_id: str):
        stmt = text("""
            SELECT count(*)
            FROM note_locks nl
            JOIN clinical_notes cn ON nl.note_id = cn.id
            WHERE cn.encounter_id = :eid
            AND nl.expires_at > now()
        """)
        result = await self.db.execute(stmt, {"eid": encounter_id})
        count = result.scalar()
        return count > 0

    async def save_seal(self, seal: EncounterSeal):
        self.db.add(seal)
        await self.db.flush()
        return seal

    async def get_seal(self, encounter_id: str):
        stmt = select(EncounterSeal).where(EncounterSeal.encounter_id == encounter_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def is_encounter_sealed(self, encounter_id: str) -> bool:
        stmt = select(EncounterSeal.id).where(EncounterSeal.encounter_id == encounter_id)
        result = await self.db.execute(stmt)
        return result.scalars().first() is not None

    async def get_encounter_org(self, encounter_id: str) -> str:
        stmt = text("SELECT organization_id FROM encounters WHERE id = :eid")
        result = await self.db.execute(stmt, {"eid": encounter_id})
        return result.scalar()

    async def get_active_organization_key(self, organization_id: str):
        stmt = (
            select(OrganizationKey)
            .where(OrganizationKey.organization_id == organization_id)
            .where(OrganizationKey.is_active == True)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_key_by_fingerprint(self, fingerprint: str):
        stmt = select(OrganizationKey).where(OrganizationKey.public_key_fingerprint == fingerprint)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def save_organization_key(self, key: OrganizationKey):
        self.db.add(key)
        await self.db.flush()
        return key

    async def deactivate_organization_keys(self, organization_id: str):
        stmt = (
            update(OrganizationKey)
            .where(OrganizationKey.organization_id == organization_id)
            .where(OrganizationKey.is_active == True)
            .values(is_active=False, retired_at=text("now()"))
        )
        await self.db.execute(stmt)

    async def update_snapshot_archival(self, snapshot_id: str, status: str, legal_hold: bool = None):
        values = {"archival_status": status}
        if legal_hold is not None:
            values["legal_hold"] = legal_hold
        stmt = update(NoteSnapshot).where(NoteSnapshot.id == snapshot_id).values(**values)
        await self.db.execute(stmt)

    async def get_retention_status(self, entity_type: str, entity_id: str):
        model = NoteSnapshot if entity_type == "snapshot" else EncounterSeal
        stmt = select(model.retention_until, model.legal_hold).where(model.id == entity_id)
        result = await self.db.execute(stmt)
        return result.mappings().first()

    # --- Institutional Backup Support ---

    async def get_latest_full_backup(self, organization_id: str):
        stmt = (
            select(BackupJob)
            .where(BackupJob.organization_id == organization_id)
            .where(BackupJob.mode == "FULL")
            .where(BackupJob.status == "COMPLETED")
            .order_by(BackupJob.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def save_backup_job(self, job: BackupJob):
        self.db.add(job)
        await self.db.flush()
        return job

    async def get_all_clinical_data(self, organization_id: str):
        """
        Gathers absolute scope for FULL backup.
        """
        # Fetch everything without time filters for FULL mode
        snapshots = (await self.db.execute(select(NoteSnapshot))).scalars().all()
        seals = (await self.db.execute(select(EncounterSeal))).scalars().all()
        keys = (await self.db.execute(select(OrganizationKey).where(OrganizationKey.organization_id == organization_id))).scalars().all()
        audit = (await self.db.execute(select(ClinicalAuditLog).order_by(ClinicalAuditLog.created_at.asc()))).scalars().all()
        outbox = (await self.db.execute(select(OutboxEvent))).scalars().all()
        idempotency = (await self.db.execute(select(IdempotencyKey))).scalars().all()
        previous_jobs = (await self.db.execute(select(BackupJob).where(BackupJob.organization_id == organization_id))).scalars().all()

        return {
            "snapshots": snapshots,
            "seals": seals,
            "keys": keys,
            "audit_log": audit,
            "outbox": outbox,
            "idempotency": idempotency,
            "backup_history": previous_jobs
        }
