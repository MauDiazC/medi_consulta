from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.pagination import pagination_params

from .repository import ClinicalSessionRepository
from .schemas import ClinicalSessionCreate
from .service import ClinicalSessionService

router = APIRouter(
    prefix="/clinical-sessions",
    tags=["clinical_sessions"],
)


def get_service(db: AsyncSession = Depends(get_db)):
    return ClinicalSessionService(
        ClinicalSessionRepository(db)
    )


@router.post("")
async def create_session(
    payload: ClinicalSessionCreate,
    service=Depends(get_service),
    user=Depends(get_current_user),
):
    """Start a new clinical session/jornada."""
    return await service.create(payload, user["org"])


@router.get("")
async def list_sessions(
    page=Depends(pagination_params),
    user=Depends(get_current_user),
    service=Depends(get_service),
):
    """List clinical sessions for your organization."""
    return await service.list(user["org"], page.limit, page.offset)


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    user=Depends(get_current_user),
    service=Depends(get_service),
):
    """Get details of a specific session."""
    return await service.get(session_id, user["org"])


@router.patch("/{session_id}/deactivate")
async def deactivate_session(
    session_id: str,
    user=Depends(get_current_user),
    service=Depends(get_service),
):
    """Close/deactivate a clinical session."""
    return await service.deactivate(session_id, user["org"])


@router.patch("/{session_id}/activate")
async def activate_session(
    session_id: str,
    user=Depends(get_current_user),
    service=Depends(get_service),
):
    """Re-open/activate a clinical session."""
    return await service.activate(session_id, user["org"])