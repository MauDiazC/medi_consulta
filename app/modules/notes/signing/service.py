import hashlib
import os
import base64
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.modules.notes.signing.models import NoteSnapshot, EncounterSeal, OrganizationKey
from app.core.models import IdempotencyKey
from app.core.events import publish_event_tx
from app.modules.notes.signing.crypto_service import load_private_key, sign_hash
from app.modules.notes.signing.snapshot_builder import build_clinical_snapshot
from app.modules.notes.signing.repository import SigningRepository
from app.modules.notes.repository import ClinicalNoteRepository
from app.modules.users.repository import UserRepository
from app.modules.notes.signing.utils import canonical_json, sha256_hex
from app.modules.notes.signing.retention_service import RetentionPolicyEngine
from app.core.audit import audit_log

class SigningApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.signing_repo = SigningRepository(db)
        self.note_repo = ClinicalNoteRepository(db)
        self.user_repo = UserRepository(db)
        self.retention_engine = RetentionPolicyEngine(db)
        self._mek = os.getenv("MASTER_ENCRYPTION_KEY", "0" * 64).encode()

    async def _check_idempotency(self, key: str) -> dict | None:
        stmt = select(IdempotencyKey).where(IdempotencyKey.id == key)
        result = await self.db.execute(stmt)
        record = result.scalars().first()
        return record.response_payload if record else None

    async def _record_idempotency(self, key: str, payload: dict):
        ik = IdempotencyKey(id=key, response_payload=payload)
        # Phase 1: Set retention for idempotency keys
        ik.retention_until = self.retention_engine.calculate_retention_period(1) # short retention
        self.db.add(ik)

    def _encrypt_key(self, plaintext_pem: str) -> str:
        aesgcm = AESGCM(bytes.fromhex(self._mek.decode()))
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext_pem.encode(), None)
        return base64.b64encode(nonce + ciphertext).decode()

    def _decrypt_key(self, encrypted_blob: str) -> bytes:
        data = base64.b64decode(encrypted_blob)
        nonce, ciphertext = data[:12], data[12:]
        aesgcm = AESGCM(bytes.fromhex(self._mek.decode()))
        return aesgcm.decrypt(nonce, ciphertext, None)

    async def get_snapshot(self, note_id: str, requestor_id: str, purpose: str = "review") -> NoteSnapshot:
        snapshot = await self.signing_repo.get_by_note_id(note_id)
        if snapshot:
            await audit_log(self.db, "note_snapshot", str(snapshot.id), "accessed", requestor_id, metadata={"purpose": purpose})
            await self.db.flush()
        return snapshot

    async def rotate_organization_key(self, organization_id: str, public_key_pem: str, private_key_pem: str, executor_id: str) -> OrganizationKey:
        fingerprint = hashlib.sha256(public_key_pem.encode()).hexdigest()
        encrypted_priv = self._encrypt_key(private_key_pem)
        
        await self.signing_repo.deactivate_organization_keys(organization_id)
        now = datetime.now(timezone.utc)
        new_key = OrganizationKey(
            organization_id=organization_id, public_key_pem=public_key_pem, public_key_fingerprint=fingerprint,
            encrypted_private_key=encrypted_priv, is_active=True,
            # Phase 1 & 3: Retention
            retention_until=self.retention_engine.calculate_retention_period(10), # Long retention for keys
            retention_source="Institutional Key Policy",
            created_at=now
        )
        await self.signing_repo.save_organization_key(new_key)
        await audit_log(self.db, "organization_key", str(new_key.id), "rotated", executor_id)
        await self.db.commit()
        return new_key

    async def execute_signing(self, note, version, signer_id: str, private_key_pem: bytes = None, idempotency_key: str = None) -> dict:
        if idempotency_key:
            prev_resp = await self._check_idempotency(idempotency_key)
            if prev_resp: return prev_resp

        if await self.signing_repo.is_encounter_sealed(str(note["encounter_id"])):
            raise ValueError("Encounter is sealed.")

        user = await self.user_repo.get(signer_id, str(note["organization_id"]))
        prof_info = {"full_name": user["full_name"], "professional_license": user.get("professional_license", "PENDING"), "role": user["role"]}

        org_id = str(note["organization_id"])
        
        # Determine which key to use
        if private_key_pem:
            priv_pem = private_key_pem
            # If signing with personal key, we use the fingerprint of the provided key
            # In a real world scenario, we'd validate this against the registered public key
            fingerprint = "personal-key-signed"
        else:
            active_key = await self.signing_repo.get_active_organization_key(org_id)
            if not active_key:
                raise ValueError("No active signing key found for organization.")
            priv_pem = self._decrypt_key(active_key.encrypted_private_key)
            fingerprint = active_key.public_key_fingerprint
            
        latest = await self.signing_repo.get_latest_snapshot_for_encounter(str(note["encounter_id"]))
        previous_hash = latest.content_hash if latest else None

        payload, content_hash = build_clinical_snapshot(note, version, prof_info, previous_snapshot_hash=previous_hash)
        private = load_private_key(priv_pem)
        signature = sign_hash(private, content_hash)

        snapshot = NoteSnapshot(
            note_id=note["id"], version_id=version["id"], snapshot_json=payload,
            content_hash=content_hash, signature=signature, signed_by=signer_id,
            signed_at=datetime.now(timezone.utc), public_key_fingerprint=fingerprint,
            previous_snapshot_hash=previous_hash,
            # Phase 3 & 5: Structural Hardening
            retention_until=self.retention_engine.calculate_retention_period(5),
            retention_source="NOM-004-SSA3-2012",
            is_immutable=True
        )
        await self.signing_repo.save_snapshot(snapshot)
        await self.note_repo.sign(note["id"])
        await audit_log(self.db, "clinical_note", str(note["id"]), "signed", signer_id)
        
        await publish_event_tx(self.db, "note.signed", {
            "encounter_id": str(note["encounter_id"]), "note_id": str(note["id"]), "snapshot_id": str(snapshot.id)
        })

        response = {"status": "signed", "snapshot_id": str(snapshot.id)}
        if idempotency_key: await self._record_idempotency(idempotency_key, response)
        
        await self.db.commit()
        return response

    async def execute_encounter_sealing(self, encounter_id: str, signer_id: str, idempotency_key: str = None) -> dict:
        if idempotency_key:
            prev_resp = await self._check_idempotency(idempotency_key)
            if prev_resp: return prev_resp

        if await self.signing_repo.get_seal(encounter_id): raise ValueError("Already sealed.")
        
        org_id = await self.signing_repo.get_encounter_org(encounter_id)
        if not org_id:
            raise ValueError("Encounter not found or has no organization.")
            
        active_key = await self.signing_repo.get_active_organization_key(str(org_id))
        if not active_key:
            raise ValueError("No active signing key found for this organization.")

        priv_pem = self._decrypt_key(active_key.encrypted_private_key)

        snapshots = await self.signing_repo.get_all_snapshots_for_encounter(encounter_id)
        if not snapshots:
            raise ValueError("Cannot seal an encounter with no signed snapshots.")

        seal_payload = {
            "encounter_id": str(encounter_id),
            "snapshot_hashes": [{"snapshot_id": str(s.id), "content_hash": s.content_hash} for s in snapshots],
            "snapshot_count": len(snapshots),
            "final_chain_hash": snapshots[-1].content_hash,
            "sealed_at": datetime.now(timezone.utc).isoformat(),
            "schema_version": "encounter-seal-v1"
        }

        aggregate_hash = sha256_hex(canonical_json(seal_payload))
        signature = sign_hash(load_private_key(priv_pem), aggregate_hash)

        seal = EncounterSeal(
            encounter_id=encounter_id, aggregate_hash=aggregate_hash, signature=signature,
            signed_at=datetime.now(timezone.utc), public_key_fingerprint=active_key.public_key_fingerprint,
            seal_payload=seal_payload,
            # Phase 3 & 5: Structural Hardening
            retention_until=self.retention_engine.calculate_retention_period(5),
            retention_source="NOM-004-SSA3-2012",
            is_immutable=True
        )
        await self.signing_repo.save_seal(seal)
        await audit_log(self.db, "encounter", str(encounter_id), "sealed", signer_id)
        await publish_event_tx(self.db, "encounter.sealed", {"encounter_id": str(encounter_id), "seal_id": str(seal.id)})

        response = {"status": "sealed", "seal_id": str(seal.id)}
        if idempotency_key: await self._record_idempotency(idempotency_key, response)

        await self.db.commit()
        return response
