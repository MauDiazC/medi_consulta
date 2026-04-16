import json
import anyio
import asyncio
import logging
from datetime import datetime
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.models import OutboxEvent
from app.core.events import publish_event
from app.modules.notes.signing.service import SigningApplicationService
from app.modules.notes.signing.pdf_render import render_snapshot_pdf
from app.modules.appointments.service import AppointmentService
from app.modules.appointments.repository import AppointmentRepository
from app.core.worker_settings import get_redis_settings

logger = logging.getLogger("worker")

# --- ARQ Tasks ---

async def handle_note_signed_task(ctx, event_data: dict):
    """
    ARQ Task: Guaranteed PDF generation.
    """
    note_id = event_data.get("note_id")
    if not note_id: return

    try:
        async with AsyncSessionLocal() as db:
            signing_service = SigningApplicationService(db)
            snapshot = await signing_service.get_snapshot(note_id, "SYSTEM", "pdf_generation")
            if not snapshot:
                logger.error(f"Snapshot not found for note: {note_id}")
                return

            # CPU bound task in thread
            pdf_bytes = await anyio.to_thread.run_sync(render_snapshot_pdf, snapshot)
            pdf_path = f"/tmp/snapshot_{snapshot.id}.pdf"
            await anyio.Path(pdf_path).write_bytes(pdf_bytes)

            snapshot.pdf_path = pdf_path
            await db.commit()
            logger.info(f"PDF generated successfully for note: {note_id}")
    except Exception as e:
        logger.error(f"PDF Worker error: {str(e)}", exc_info=True)
        raise e # ARQ will retry if exception is raised

# --- Background Loops ---

async def run_appointment_scheduler():
    while True:
        try:
            async with AsyncSessionLocal() as db:
                service = AppointmentService(AppointmentRepository(db))
                await service.process_pending_reminders()
        except Exception as e:
            logger.error(f"Appointment scheduler error: {str(e)}", exc_info=True)
        await asyncio.sleep(60)

async def relay_outbox_events():
    """
    Polls outbox_events and:
    1. Publishes to Pub/Sub (for real-time updates/cache invalidation).
    2. Enqueues to ARQ (for heavy/critical background tasks).
    """
    from arq import create_pool
    arq_pool = await create_pool(get_redis_settings())

    while True:
        try:
            async with AsyncSessionLocal() as db:
                # Optimized query for outbox
                stmt = select(OutboxEvent).where(OutboxEvent.processed == False).limit(20)
                result = await db.execute(stmt)
                events = result.scalars().all()

                for event in events:
                    # 1. PubSub for real-time notifications/UI
                    await publish_event(event.event_type, event.payload)
                    
                    # 2. ARQ for reliable heavy tasks
                    if event.event_type == "note.signed":
                        await arq_pool.enqueue_job('handle_note_signed_task', event.payload)
                    
                    event.processed = True
                    event.processed_at = datetime.utcnow()
                
                if events:
                    await db.commit()
        except Exception as e:
            logger.error(f"Outbox relay error: {str(e)}", exc_info=True)
        
        await asyncio.sleep(1)

# --- ARQ Worker Configuration ---

class WorkerSettings:
    """
    Configuration for the ARQ worker process.
    Run with: arq app.worker.realtime_worker.WorkerSettings
    """
    functions = [handle_note_signed_task]
    redis_settings = get_redis_settings()
    
    @staticmethod
    async def on_startup(ctx):
        logger.info("ARQ Worker starting...")
        # Start our custom loops in the background within the ARQ process
        ctx['scheduler_task'] = asyncio.create_task(run_appointment_scheduler())
        ctx['outbox_task'] = asyncio.create_task(relay_outbox_events())

    @staticmethod
    async def on_shutdown(ctx):
        logger.info("ARQ Worker shutting down...")
        if 'scheduler_task' in ctx:
            ctx['scheduler_task'].cancel()
        if 'outbox_task' in ctx:
            ctx['outbox_task'].cancel()

if __name__ == "__main__":
    # Fallback to run manually if needed, but 'arq' command is preferred
    import uvicorn
    print("Use 'arq app.worker.realtime_worker.WorkerSettings' to run this worker.")
