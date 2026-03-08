from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_role

from .repository import SessionRepository
from .service import SessionService

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
)


def get_service(db: AsyncSession = Depends(get_db)):
    return SessionService(
        SessionRepository(db)
    )


@router.post("/encounter/{encounter_id}/open")
async def open_session(
    encounter_id: str,
    user=Depends(
        require_role("doctor", "assistant")
    ),
    service=Depends(get_service),
):
    return await service.open_session(
        encounter_id,
        user["sub"],
    )


@router.post("/{session_id}/heartbeat")
async def heartbeat(
    session_id: str,
    service=Depends(get_service),
):
    await service.heartbeat(session_id)
    return {"alive": True}


@router.post("/{session_id}/close")
async def close_session(
    session_id: str,
    service=Depends(get_service),
):
    await service.close(session_id)
    return {"closed": True}
