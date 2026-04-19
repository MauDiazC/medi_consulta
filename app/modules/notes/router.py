import asyncio

from fastapi import APIRouter, Depends, Header, File, UploadFile, Request, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.note_locks import acquire_note_lock, release_note_lock
from app.core.audit import background_audit, RequestAuditContext
from app.core.permissions import require_role

from .repository import ClinicalNoteRepository
from .service import ClinicalNoteService

router = APIRouter(
    prefix="/notes",
    tags=["notes"],
)


def get_service(
    db: AsyncSession = Depends(get_db),
):
    return ClinicalNoteService(
        ClinicalNoteRepository(db)
    )

@router.get("/encounter/{encounter_id}")
async def list_notes_by_encounter(
    encounter_id: str,
    user=Depends(get_current_user),
    service=Depends(get_service),
):
    """Lists all note versions for a specific encounter."""
    return await service.repo.list_by_encounter(encounter_id, user["org"])

@router.get("/{note_id}")
async def get_note(
    note_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
    service=Depends(get_service),
    db=Depends(get_db),
):
    """
    Retrieves a clinical note by ID.
    Audits access for compliance (SaaS/HIPAA standard).
    """
    note = await service.repo.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Nota clínica no encontrada.")
    
    # Professional Audit: Log access in background
    ctx = RequestAuditContext(request, user)
    background_audit(
        background_tasks,
        get_db, # Factory for fresh session
        entity="clinical_note",
        entity_id=note_id,
        action="READ_ACCESS",
        user_id=ctx.user_id,
        organization_id=ctx.organization_id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
        metadata={"encounter_id": str(note["encounter_id"])}
    )

    return note


@router.post("/autosave/{encounter_id}")
async def autosave_note(
    encounter_id: str,
    payload: dict,
    if_unmodified_since: str = Header(...),
    user=Depends(get_current_user),
    service=Depends(get_service),
):
    return await service.autosave(
        encounter_id,
        user["sub"],
        user["org"],
        payload,
        if_unmodified_since,
    )


@router.post("/finalize/{encounter_id}")
async def finalize_version(
    encounter_id: str,
    user=Depends(get_current_user),
    service=Depends(get_service),
):
    return await service.finalize_version(
        encounter_id,
        user["sub"],
        user["org"],
    )



@router.post("/{note_id}/sign")
async def sign_note(
    note_id: str,
    keyfile: UploadFile = File(...),
    user=Depends(get_current_user),
    service=Depends(get_service),
):
    private_pem = await keyfile.read()
    return await service.sign(
        note_id,
        user["sub"],
        user["org"],
        private_pem
    )


@router.post("/lock/{note_id}")
async def lock_note(
    note_id: str,
    x_session_id: str = Header(...),
    user=Depends(get_current_user),
):
    return await acquire_note_lock(
        note_id,
        user["sub"],
        x_session_id,
    )


@router.post("/unlock/{note_id}")
async def unlock_note(
    note_id: str,
    x_session_id: str = Header(...),
    user=Depends(get_current_user),
):
    return await release_note_lock(
        note_id,
        user["sub"],
        x_session_id,
    )


@router.post("/ai/stream/{encounter_id}")
async def stream_ai(
    encounter_id: str,
    user=Depends(require_role("doctor")),
):

    async def generator():

        chunks = [
            "Paciente refiere...",
            "Exploración física...",
            "Impresión clínica...",
            "Plan terapéutico...",
        ]

        for chunk in chunks:
            await asyncio.sleep(1)
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
    )

from fastapi.responses import StreamingResponse, Response
from weasyprint import HTML
import io

@router.get("/{note_id}/prescription")
async def generate_prescription_pdf(
    note_id: str,
    user=Depends(get_current_user),
    service=Depends(get_service),
    db=Depends(get_db)
):
    """
    Generates a professional PDF prescription based on the clinical note's plan.
    Includes doctor's license and patient data.
    """
    # 1. Fetch full data
    note = await service.repo.get(note_id, user["org"])
    if not note:
        raise HTTPException(404, "Note not found")

    from app.modules.notes.signing.identity_repository import ProfessionalIdentityRepository
    ident_repo = ProfessionalIdentityRepository(db)
    identity = await ident_repo.get_by_user(str(note["created_by"]), user["org"])

    from app.modules.encounters.repository import EncounterRepository
    enc_repo = EncounterRepository(db)
    encounter = await enc_repo.get(str(note["encounter_id"]), user["org"])

    # 2. HTML Template for the Prescription
    html_content = f"""
    <html>
        <head>
            <style>
                body {{ font-family: sans-serif; padding: 40px; color: #333; }}
                .header {{ border-bottom: 2px solid #0056b3; padding-bottom: 10px; margin-bottom: 20px; }}
                .doctor-name {{ font-size: 20px; font-weight: bold; color: #0056b3; }}
                .license {{ font-size: 12px; color: #666; }}
                .patient-info {{ background: #f4f4f4; padding: 10px; margin-bottom: 30px; border-radius: 5px; }}
                .rx-title {{ font-size: 18px; border-bottom: 1px solid #ccc; margin-bottom: 10px; padding-bottom: 5px; }}
                .plan {{ line-height: 1.6; font-size: 14px; white-space: pre-wrap; }}
                .footer {{ margin-top: 50px; font-size: 10px; text-align: center; color: #999; border-top: 1px solid #eee; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="doctor-name">Dr. {identity["full_name"] if identity else user.get("full_name", "Médico Tratante")}</div>
                <div class="license">Cédula Profesional: {identity["license_number"] if identity else "N/A"}</div>
                <div class="specialty">{identity["specialty"] if identity else ""}</div>
            </div>
            
            <div class="patient-info">
                <strong>Paciente:</strong> {encounter["patient_name"] if encounter else "N/A"} <br>
                <strong>Fecha:</strong> {note["created_at"].strftime("%d/%m/%Y")}
            </div>

            <div class="rx-title">Indicaciones Médicas (Rx)</div>
            <div class="plan">{note["plan"]}</div>

            <div class="footer">
                Documento generado electrónicamente por Mediconsulta. <br>
                Este documento es una receta médica digital válida.
            </div>
        </body>
    </html>
    """

    # 3. Convert HTML to PDF
    pdf_bytes = HTML(string=html_content).write_pdf()
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=receta_{note_id}.pdf"}
    )

@router.get("/diff/{encounter_id}/{v1}/{v2}")
async def diff_versions(
    encounter_id: str,
    v1: int,
    v2: int,
    service=Depends(get_service),
):
    return await service.diff_versions(
        encounter_id,
        v1,
        v2,
    )