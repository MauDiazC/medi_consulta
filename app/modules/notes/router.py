import asyncio

from fastapi import APIRouter, Depends, Header, File, UploadFile, Request, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.note_locks import acquire_note_lock, release_note_lock
from app.core.audit import background_audit, RequestAuditContext

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

@router.get(
    "/diff/{encounter_id}/{v1}/{v2}"
)
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