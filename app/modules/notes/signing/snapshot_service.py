from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notes.signing.models import NoteSnapshot
from app.modules.notes.signing.crypto_service import load_private_key, sign_hash
from app.modules.notes.signing.snapshot_builder import build_clinical_snapshot


async def sign_note(
    db: AsyncSession,
    note,
    version,
    signer_id: str,
    private_key_pem: bytes,
):
    # 1) Construir snapshot
    payload, content_hash = build_clinical_snapshot(note, version)

    # 2) Cargar llave
    private = load_private_key(private_key_pem)

    # 3) Firmar
    signature = sign_hash(private, content_hash)

    # 4) Guardar
    snapshot = NoteSnapshot(
        note_id=note.id,
        version_id=version.id,
        snapshot_json=payload,
        content_hash=content_hash,
        signature=signature,
        signed_by=signer_id,
        signed_at=datetime.utcnow(),
        public_key_fingerprint="org-rsa-fingerprint",  # placeholder
    )
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)
    return snapshot