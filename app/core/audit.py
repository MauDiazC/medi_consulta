import hashlib
import json
from datetime import datetime
from sqlalchemy import text, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.notes.signing.utils import canonical_json, sha256_hex

async def audit_log(
    db: AsyncSession,
    entity: str,
    entity_id: str,
    action: str,
    user_id: str,
    metadata: dict | None = None,
):
    """
    Creates a cryptographically chained audit log entry.
    """
    # 1) Fetch latest hash for the chain (Previous Entry)
    stmt = text("""
        SELECT entry_hash 
        FROM clinical_audit_log 
        ORDER BY created_at DESC, id DESC 
        LIMIT 1
    """)
    result = await db.execute(stmt)
    previous_hash = result.scalar()

    # 2) Prepare entry data
    entry_data = {
        "entity": entity,
        "entity_id": str(entity_id),
        "action": action,
        "performed_by": str(user_id),
        "metadata": metadata or {},
        "previous_hash": previous_hash,
        "created_at": datetime.utcnow().isoformat()
    }

    # 3) Compute entry hash (Canonical JSON ensures determinism)
    canonical = canonical_json(entry_data)
    entry_hash = sha256_hex(canonical)

    # 4) Persist entry
    await db.execute(
        text("""
        INSERT INTO clinical_audit_log (
            entity,
            entity_id,
            action,
            performed_by,
            metadata,
            previous_hash,
            entry_hash,
            created_at
        )
        VALUES (
            :entity,
            :entity_id,
            :action,
            :performed_by,
            :metadata,
            :previous_hash,
            :entry_hash,
            :created_at
        )
        """),
        {
            **entry_data,
            "entry_hash": entry_hash
        },
    )
    # Note: Service layer manages commit for atomicity