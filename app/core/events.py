import json
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import OutboxEvent
from app.core.config import settings

r = redis.from_url(settings.REDIS_URL)


async def publish_event(event: str, payload: dict):
    """
    Immediate publication (legacy/infrastructure only).
    """
    await r.publish(
        "mediconsulta.events",
        json.dumps({
            "type": event,
            "data": payload
        }),
    )

async def publish_event_tx(db: AsyncSession, event_type: str, payload: dict):
    """
    Hardening: Transactional Outbox Pattern.
    Persists the event inside the current database transaction.
    """
    event = OutboxEvent(
        event_type=event_type,
        payload=payload
    )
    db.add(event)
    # No flush/commit here; let the service manage the lifecycle.