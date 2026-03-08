from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_role

from .repository import CopilotRepository
from .service import CopilotService

router = APIRouter(
    prefix="/copilot",
    tags=["copilot"],
)


def get_service(db: AsyncSession = Depends(get_db)):
    return CopilotService(
        CopilotRepository(db)
    )


@router.post("/analyze/{note_id}")
async def analyze_note(
    note_id: str,
    payload: dict,
    user=Depends(
        require_role("doctor", "assistant")
    ),
    service=Depends(get_service),
):
    return await service.process_snapshot(
        note_id,
        payload["session_id"],
        payload,
    )


@router.get("/{note_id}")
async def get_suggestions(
    note_id: str,
    service=Depends(get_service),
):
    return await service.suggestions(note_id)
