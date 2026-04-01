import json
import uuid
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import OutboxEvent
from app.core.config import settings

# Global redis client (Lazy initialization)
_r = None

def get_redis():
    global _r
    if _r is None:
        if settings.REDIS_URL == "mock":
            return None
        _r = redis.from_url(settings.REDIS_URL)
    return _r

class EventEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)

async def publish_event(event: str, payload: dict):
    """
    Immediate publication (legacy/infrastructure only).
    """
    r = get_redis()
    if r is None:
        return

    await r.publish(
        "mediconsulta.events",
        json.dumps({
            "type": event,
            "data": payload
        }, cls=EventEncoder),
    )

async def publish_event_tx(db: AsyncSession, event_type: str, payload: dict):
    """
    Hardening: Transactional Outbox Pattern.
    Persists the event inside the current database transaction.
    """
    # Sanitize payload for JSON column
    sanitized_payload = json.loads(json.dumps(payload, cls=EventEncoder))

    event = OutboxEvent(
        event_type=event_type,
        payload=sanitized_payload
    )
    db.add(event)