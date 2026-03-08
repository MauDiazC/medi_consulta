import asyncio

from fastapi import APIRouter, Depends, Header, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.note_locks import acquire_note_lock, release_note_lock

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
        user["id"],
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
        user["id"],
    )


from fastapi import APIRouter, Depends, Header, File, UploadFile
...
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
        user["id"],
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
        user["id"],
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
        user["id"],
        x_session_id,
    )


@router.post("/ai/stream/{encounter_id}")
async def stream_ai(
    encounter_id: str,
    user=Depends(get_current_user),
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