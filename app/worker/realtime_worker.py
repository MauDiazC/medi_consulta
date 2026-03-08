import json
import anyio
import asyncio
import redis.asyncio as redis
import logging
from datetime import datetime
from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.core.models import OutboxEvent
from app.core.events import publish_event
from app.modules.notes.signing.service import SigningApplicationService
from app.modules.notes.signing.pdf_render import render_snapshot_pdf
from app.core.config import settings

r = redis.from_url(settings.REDIS_URL)
logger = logging.getLogger("worker")

async def relay_outbox_events():
    """
    Guaranteed Relay: Polls outbox_events and publishes to Redis.
    """
    while True:
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(OutboxEvent).where(OutboxEvent.processed == False).limit(10)
                result = await db.execute(stmt)
                events = result.scalars().all()

                for event in events:
                    await publish_event(event.event_type, event.payload)
                    event.processed = True
                    event.processed_at = datetime.utcnow()
                
                await db.commit()
        except Exception as e:
            logger.error(f"Outbox relay error: {str(e)}", exc_info=True)
        
        await asyncio.sleep(1)

async def handle_note_signed(event_data: dict):
    note_id = event_data.get("note_id")
    org_id = event_data.get("organization_id")
    if not note_id: return

    try:
        async with AsyncSessionLocal() as db:
            signing_service = SigningApplicationService(db)
            snapshot = await signing_service.get_snapshot(note_id, "SYSTEM", "pdf_generation")
            if not snapshot:
                logger.error(f"Snapshot not found for note: {note_id}", extra={"note_id": note_id, "event_type": "note.signed"})
                return

            pdf_bytes = await anyio.to_thread.run_sync(render_snapshot_pdf, snapshot)
            pdf_path = f"/tmp/snapshot_{snapshot.id}.pdf"
            await anyio.Path(pdf_path).write_bytes(pdf_bytes)

            snapshot.pdf_path = pdf_path
            await db.commit()
    except Exception as e:
        logger.error(
            f"PDF Worker error: {str(e)}", 
            exc_info=True, 
            extra={
                "event_type": "note.signed", 
                "note_id": note_id,
                "organization_id": org_id
            }
        )

async def run_listener():
    pubsub = r.pubsub()
    await pubsub.subscribe("mediconsulta.events")
    logger.info("Redis subscription established")

    async for message in pubsub.listen():
        if message["type"] != "message": continue

        event = json.loads(message["data"])
        event_type = event.get("type")
        event_data = event.get("data", {})
        
        # Approved Metadata Extraction
        correlation_id = event.get("correlation_id")
        organization_id = event_data.get("organization_id")

        logger.info(
            f"Message received: {event_type}", 
            extra={
                "event_type": event_type, 
                "correlation_id": correlation_id, 
                "organization_id": organization_id
            }
        )

        # Workspace cache logic
        encounter_id = event_data.get("encounter_id")
        if encounter_id:
            await r.delete(f"workspace:{encounter_id}")
            await r.publish(f"workspace_updates:{encounter_id}", json.dumps(event))

        if event_type == "note.signed":
            await handle_note_signed(event_data)
            
        logger.info(
            "Message processed", 
            extra={
                "event_type": event_type, 
                "correlation_id": correlation_id, 
                "organization_id": organization_id
            }
        )

async def run():
    """
    Main worker entry point.
    """
    logger.info("Worker started")
    await asyncio.gather(
        run_listener(),
        relay_outbox_events()
    )

if __name__ == "__main__":
    from app.core.logging import configure_logging
    configure_logging()
    
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
