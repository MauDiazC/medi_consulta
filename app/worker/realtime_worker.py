import json
import anyio
import asyncio
import logging
import resend
from datetime import datetime, timezone
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.models import OutboxEvent
from app.core.events import publish_event
from app.modules.notes.signing.service import SigningApplicationService
from app.modules.notes.signing.pdf_render import render_snapshot_pdf
from app.modules.appointments.service import AppointmentService
from app.modules.appointments.repository import AppointmentRepository
from app.core.worker_settings import get_redis_settings
from app.core.config import settings

logger = logging.getLogger("worker")

# Initialize Resend
resend.api_key = settings.RESEND_API_KEY

# --- ARQ Tasks ---

async def handle_login_notification_task(ctx, event_data: dict):
    """
    ARQ Task: Sends a security notification email on successful login.
    """
    to_email = event_data.get("to")
    metadata = event_data.get("metadata", {})
    
    try:
        html_content = f"""
        <h2>Nuevo inicio de sesión detectado</h2>
        <p>Hola, se ha detectado un nuevo inicio de sesión en tu cuenta de Mediconsulta.</p>
        <ul>
            <li><b>Fecha:</b> {metadata.get('timestamp')}</li>
            <li><b>Navegador:</b> {metadata.get('user_agent')}</li>
            <li><b>IP:</b> {metadata.get('host')}</li>
        </ul>
        <p>Si no fuiste tú, por favor contacta a soporte de inmediato.</p>
        """
        
        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": to_email,
            "subject": "Seguridad: Nuevo inicio de sesión",
            "html": html_content
        })
        logger.info(f"Login notification email sent to {to_email}")
    except Exception as e:
        logger.error(f"Error sending login email: {str(e)}")
        raise e

async def handle_password_reset_task(ctx, event_data: dict):
    """
    ARQ Task: Sends a password reset link to the user.
    """
    to_email = event_data.get("to")
    token = event_data.get("token")
    
    try:
        # En una app real, aquí pondrías la URL de tu frontend
        reset_url = f"https://app.mediconsulta.com/reset-password?token={token}"
        
        html_content = f"""
        <h2>Recuperación de Contraseña</h2>
        <p>Has solicitado restablecer tu contraseña en Mediconsulta.</p>
        <p>Haz clic en el siguiente enlace para continuar:</p>
        <a href="{reset_url}" style="padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">Restablecer Contraseña</a>
        <p>Este enlace expirará en 60 minutos.</p>
        <p>Si no solicitaste este cambio, puedes ignorar este correo.</p>
        """
        
        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": to_email,
            "subject": "Recuperación de contraseña - Mediconsulta",
            "html": html_content
        })
        logger.info(f"Password reset email sent to {to_email}")
    except Exception as e:
        logger.error(f"Error sending reset email: {str(e)}")
        raise e

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
                    elif event.event_type == "auth.login_notification":
                        await arq_pool.enqueue_job('handle_login_notification_task', event.payload)
                    elif event.event_type == "auth.password_reset":
                        await arq_pool.enqueue_job('handle_password_reset_task', event.payload)
                    
                    event.processed = True
                    event.processed_at = datetime.now(timezone.utc)
                
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
    functions = [
        handle_note_signed_task, 
        handle_login_notification_task, 
        handle_password_reset_task
    ]
    redis_settings = get_redis_settings()
    
    @staticmethod
    async def on_startup(ctx):
        logger.info("ARQ Worker starting...")
        # Start our custom loops in the background within the ARQ process
        ctx['outbox_task'] = asyncio.create_task(relay_outbox_events())

    @staticmethod
    async def on_shutdown(ctx):
        logger.info("ARQ Worker shutting down...")
        if 'outbox_task' in ctx:
            ctx['outbox_task'].cancel()

if __name__ == "__main__":
    # Fallback to run manually if needed, but 'arq' command is preferred
    import uvicorn
    print("Use 'arq app.worker.realtime_worker.WorkerSettings' to run this worker.")
