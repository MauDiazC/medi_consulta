import json
import uuid
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import OutboxEvent
from app.core.config import settings

r = redis.from_url(settings.REDIS_URL)

class EventEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)

async def publish_event(event: str, payload: dict):
    """
    Immediate publication (legacy/infrastructure only).
    """
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