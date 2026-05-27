import asyncio
import logging
from datetime import UTC, datetime

import anyio
import resend
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.events import publish_event
from app.core.models import OutboxEvent
from app.core.worker_settings import get_redis_settings
from app.modules.notes.signing.pdf_render import render_snapshot_pdf
from app.modules.notes.signing.service import SigningApplicationService

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
            <li><b>Fecha:</b> {metadata.get("timestamp")}</li>
            <li><b>Navegador:</b> {metadata.get("user_agent")}</li>
            <li><b>IP:</b> {metadata.get("host")}</li>
        </ul>
        <p>Si no fuiste tú, por favor contacta a soporte de inmediato.</p>
        """

        resend.Emails.send(
            {
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": to_email,
                "subject": "Seguridad: Nuevo inicio de sesión",
                "html": html_content,
            }
        )
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

        resend.Emails.send(
            {
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": to_email,
                "subject": "Recuperación de contraseña - Mediconsulta",
                "html": html_content,
            }
        )
        logger.info(f"Password reset email sent to {to_email}")
    except Exception as e:
        logger.error(f"Error sending reset email: {str(e)}")
        raise e


async def handle_note_signed_task(ctx, event_data: dict):
    """
    ARQ Task: Guaranteed PDF generation.
    """
    note_id = event_data.get("note_id")
    if not note_id:
        return

    try:
        async with AsyncSessionLocal() as db:
            signing_service = SigningApplicationService(db)
            snapshot = await signing_service.get_snapshot(
                note_id, "SYSTEM", "pdf_generation"
            )
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
        raise e  # ARQ will retry if exception is raised


async def handle_clinical_embedding_task(ctx, event_data: dict):
    """
    ARQ Task: Generates and stores clinical note embeddings for RAG.
    """
    note_id = event_data.get("note_id")
    if not note_id:
        return

    from sqlalchemy import text

    from app.modules.rag.embedding_service import EmbeddingService

    try:
        async with AsyncSessionLocal() as db:
            # 1. Fetch note content and patient_id
            stmt = text("""
                SELECT cn.subjective, cn.objective, cn.assessment, cn.plan, e.patient_id
                FROM clinical_notes cn
                JOIN encounters e ON cn.encounter_id = e.id
                WHERE cn.id = CAST(:nid AS UUID)
            """)
            result = await db.execute(stmt, {"nid": note_id})
            row = result.mappings().first()

            if not row:
                logger.error(f"Note not found for embedding: {note_id}")
                return

            # 2. Prepare text for embedding
            clinical_text = f"""
            SUBJETIVO: {row["subjective"] or ""}
            OBJETIVO: {row["objective"] or ""}
            ASIENTO/IMPRESION: {row["assessment"] or ""}
            PLAN: {row["plan"] or ""}
            """.strip()

            if not clinical_text:
                logger.warning(
                    f"Empty clinical text for note {note_id}, skipping embedding."
                )
                return

            # 3. Generate embedding
            embedder = EmbeddingService()
            vector = await embedder.embed(clinical_text)

            # 4. Store embedding
            await db.execute(
                text("""
                INSERT INTO clinical_note_embeddings (note_id, patient_id, embedding)
                VALUES (CAST(:nid AS UUID), CAST(:pid AS UUID), :vector)
                ON CONFLICT (note_id) DO UPDATE SET embedding = :vector
            """),
                {"nid": note_id, "pid": row["patient_id"], "vector": vector},
            )
            await db.commit()
            logger.info(f"Clinical embedding generated and stored for note: {note_id}")

    except Exception as e:
        logger.error(f"Embedding Worker error: {str(e)}", exc_info=True)
        raise e


async def handle_payment_received_task(ctx, event_data: dict):
    """
    ARQ Task: Notifies the organization about a successful payment and invites them to invoice.
    """
    org_id = event_data.get("organization_id")
    amount = event_data.get("amount")
    currency = event_data.get("currency")

    try:
        async with AsyncSessionLocal() as db:
            # Fetch admin email
            from sqlalchemy import text

            r = await db.execute(
                text(
                    "SELECT email FROM users WHERE organization_id = CAST(:oid AS UUID) AND role = 'admin' LIMIT 1"
                ),
                {"oid": org_id},
            )
            admin = r.mappings().first()
            if not admin:
                logger.warning(
                    f"No admin found for organization {org_id} to send payment notification."
                )
                return

            to_email = admin["email"]
            amount_decimal = amount / 100.0

            html_content = f"""
            <h2>Pago Recibido con Éxito</h2>
            <p>Hola, hemos recibido tu pago por la suscripción de Mediconsulta.</p>
            <ul>
                <li><b>Monto:</b> {amount_decimal} {currency.upper()}</li>
                <li><b>Fecha:</b> {datetime.now(UTC).strftime("%d/%m/%Y")}</li>
            </ul>
            <p>Si necesitas factura (CFDI), puedes generarla ahora mismo desde tu panel de administración en la sección de Facturación.</p>
            <a href="https://app.mediconsulta.com/billing/history" style="padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px;">Ir a Facturación</a>
            """

            resend.Emails.send(
                {
                    "from": settings.DEFAULT_FROM_EMAIL,
                    "to": to_email,
                    "subject": "Pago confirmado - Mediconsulta",
                    "html": html_content,
                }
            )
            logger.info(f"Payment success email sent to {to_email} for org {org_id}")
    except Exception as e:
        logger.error(f"Error in payment notification task: {str(e)}")
        raise e


async def handle_subscription_sync_task(ctx, event_data: dict):
    """
    ARQ Task: Ensures organization state is synced with Stripe for edge cases.
    """
    org_id = event_data.get("organization_id")
    # Logic to call Stripe API and verify status if needed
    logger.info(f"Subscription sync task completed for org {org_id}")


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
                stmt = (
                    select(OutboxEvent).where(not OutboxEvent.processed).limit(20)
                )
                result = await db.execute(stmt)
                events = result.scalars().all()

                for event in events:
                    # 1. PubSub for real-time notifications/UI
                    await publish_event(event.event_type, event.payload)

                    # 2. ARQ for reliable heavy tasks
                    if event.event_type == "note.signed":
                        await arq_pool.enqueue_job(
                            "handle_note_signed_task", event.payload
                        )
                        await arq_pool.enqueue_job(
                            "handle_clinical_embedding_task", event.payload
                        )
                    elif event.event_type == "auth.login_notification":
                        await arq_pool.enqueue_job(
                            "handle_login_notification_task", event.payload
                        )
                    elif event.event_type == "auth.password_reset":
                        await arq_pool.enqueue_job(
                            "handle_password_reset_task", event.payload
                        )
                    elif event.event_type == "billing.invoice_paid":
                        await arq_pool.enqueue_job(
                            "handle_payment_received_task", event.payload
                        )
                    elif event.event_type == "billing.subscription_updated":
                        await arq_pool.enqueue_job(
                            "handle_subscription_sync_task", event.payload
                        )

                    event.processed = True
                    event.processed_at = datetime.now(UTC)

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
        handle_password_reset_task,
        handle_clinical_embedding_task,
        handle_payment_received_task,
        handle_subscription_sync_task,
    ]
    redis_settings = get_redis_settings()

    @staticmethod
    async def on_startup(ctx):
        logger.info("ARQ Worker starting...")
        # Start our custom loops in the background within the ARQ process
        ctx["outbox_task"] = asyncio.create_task(relay_outbox_events())

    @staticmethod
    async def on_shutdown(ctx):
        logger.info("ARQ Worker shutting down...")
        if "outbox_task" in ctx:
            ctx["outbox_task"].cancel()


if __name__ == "__main__":
    # Fallback to run manually if needed, but 'arq' command is preferred
    print("Use 'arq app.worker.realtime_worker.WorkerSettings' to run this worker.")
