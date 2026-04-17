import hashlib
import json
import logging
from datetime import datetime, timezone
from fastapi import Request, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.notes.signing.utils import canonical_json, sha256_hex

logger = logging.getLogger("core.audit")

class RequestAuditContext:
    """Helper to extract audit context from a FastAPI Request."""
    def __init__(self, request: Request, user: dict):
        self.user_id = user.get("id")
        self.organization_id = user.get("organization_id")
        self.ip_address = request.client.host if request.client else "unknown"
        self.user_agent = request.headers.get("user-agent", "unknown")

async def audit_log(
    db: AsyncSession,
    entity: str,
    entity_id: str,
    action: str,
    user_id: str,
    organization_id: str = None,
    ip_address: str = None,
    user_agent: str = None,
    metadata: dict | None = None,
):
    """
    Creates a cryptographically chained audit log entry with SaaS tracking.
    """
    try:
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
        now = datetime.now(timezone.utc)
        entry_data = {
            "entity": entity,
            "entity_id": str(entity_id),
            "action": action,
            "performed_by": str(user_id),
            "organization_id": str(organization_id) if organization_id else None,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "metadata": metadata or {},
            "previous_hash": previous_hash,
            "created_at": now.isoformat()
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
                organization_id,
                ip_address,
                user_agent,
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
                :organization_id,
                :ip_address,
                :user_agent,
                :metadata,
                :previous_hash,
                :entry_hash,
                :created_at
            )
            """),
            {
                **entry_data,
                "metadata": json.dumps(entry_data["metadata"]),
                "entry_hash": entry_hash,
                "created_at": now
            },
        )
        await db.commit()
    except Exception as e:
        logger.error(f"Audit Log Error: {str(e)}")
        # In audit, we log the error but don't break the main flow 
        # unless it's a critical safety system.

def background_audit(
    background_tasks: BackgroundTasks,
    db_factory, # Callable that returns a session
    **kwargs
):
    """Utility to fire audit logs in the background."""
    async def run_audit():
        async with db_factory() as db:
            await audit_log(db, **kwargs)
            
    background_tasks.add_task(run_audit)
