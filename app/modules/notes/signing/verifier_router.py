import hmac
import hashlib
from fastapi import APIRouter, Depends, Query, File, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.modules.notes.signing.models import NoteSnapshot, EncounterSeal, OrganizationKey
from app.modules.notes.signing.crypto_service import load_public_key, verify_signature
from app.modules.notes.signing.utils import canonical_json, sha256_hex
from app.modules.notes.signing.repository import SigningRepository

router = APIRouter(prefix="/verify", tags=["verification"])

async def get_authorized_key(repo: SigningRepository, fingerprint: str) -> str:
    """
    Retrieves the managed public key from the database. 
    Prevents the use of unauthorized external keys.
    """
    key_record = await repo.get_key_by_fingerprint(fingerprint)
    if not key_record:
        raise HTTPException(403, f"Public key with fingerprint {fingerprint} is not authorized by the organization.")
    return key_record.public_key_pem

@router.post("/snapshot/{snapshot_id}")
async def verify_snapshot(
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
):
    # 1) Identity Resolution
    snapshot = await db.get(NoteSnapshot, snapshot_id)
    if not snapshot:
        raise HTTPException(404, "Snapshot not found")

    # 2) Payload Integrity
    payload = snapshot.snapshot_json
    if not payload or not isinstance(payload, dict):
        raise HTTPException(422, "Invalid snapshot payload")

    # 3) Authorized Key Retrieval
    repo = SigningRepository(db)
    public_key_pem = await get_authorized_key(repo, snapshot.public_key_fingerprint)

    # 4) Fingerprint Validation
    actual_fingerprint = hashlib.sha256(public_key_pem.encode()).hexdigest()
    fingerprint_ok = hmac.compare_digest(actual_fingerprint, snapshot.public_key_fingerprint)

    # 5) Hash Integrity
    canonical = canonical_json(payload)
    recalculated = sha256_hex(canonical)
    integrity_ok = hmac.compare_digest(recalculated, snapshot.content_hash)

    # 6) Signature Verification
    signature_ok = False
    if integrity_ok and fingerprint_ok:
        try:
            public = load_public_key(public_key_pem.encode())
            signature_ok = verify_signature(public, recalculated, snapshot.signature)
        except Exception as e:
            signature_ok = False
            error_detail = str(e)
        else:
            error_detail = None
    else:
        error_detail = "Integrity or fingerprint check failed before signature verification"

    return {
        "valid": (integrity_ok and signature_ok and fingerprint_ok),
        "integrity_ok": integrity_ok,
        "signature_ok": signature_ok,
        "fingerprint_ok": fingerprint_ok,
        "diagnostics": {
            "recalculated_hash": recalculated,
            "stored_hash": snapshot.content_hash,
            "error_detail": error_detail
        },
        "details": {
            "fingerprint": snapshot.public_key_fingerprint
        }
    }

@router.post("/encounter-seal/{encounter_id}")
async def verify_encounter_seal(
    encounter_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SigningRepository(db)
    seal = await repo.get_seal(encounter_id)
    if not seal:
        raise HTTPException(404, "Encounter seal not found")

    # 1) Authorized Key Retrieval
    public_key_pem = await get_authorized_key(repo, seal.public_key_fingerprint)

    # 2) Aggregate Hash Integrity
    canonical = canonical_json(seal.seal_payload)
    recalculated_agg_hash = sha256_hex(canonical)
    integrity_ok = hmac.compare_digest(recalculated_agg_hash, seal.aggregate_hash)

    # 3) Longitudinal Validation
    current_snapshots = await repo.get_all_snapshots_for_encounter(encounter_id)
    payload_hashes = seal.seal_payload.get("snapshot_hashes", [])
    count_ok = (len(current_snapshots) == seal.seal_payload.get("snapshot_count"))
    
    list_integrity_ok = True
    if count_ok:
        for i, s in enumerate(current_snapshots):
            if str(s.id) != payload_hashes[i]["snapshot_id"] or \
               s.content_hash != payload_hashes[i]["content_hash"]:
                list_integrity_ok = False
                break
    else:
        list_integrity_ok = False

    # 4) Signature Verification
    signature_ok = False
    if integrity_ok:
        try:
            public = load_public_key(public_key_pem.encode())
            signature_ok = verify_signature(public, recalculated_agg_hash, seal.signature)
        except Exception:
            signature_ok = False

    return {
        "valid": (integrity_ok and signature_ok and list_integrity_ok),
        "integrity_ok": integrity_ok,
        "signature_ok": signature_ok,
        "snapshot_list_match": list_integrity_ok,
        "details": {
            "fingerprint": seal.public_key_fingerprint,
            "sealed_at": seal.signed_at.isoformat()
        }
    }