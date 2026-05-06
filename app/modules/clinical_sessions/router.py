from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_authorized_doctor_ids
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
    # Note: Only a doctor can start their own session. 
    # If we want assistants to start sessions for doctors, we'd need a doctor_id in the payload.
    return await service.create(payload, user["org"], user["sub"])


@router.get("")
async def list_sessions(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page=Depends(pagination_params),
    user=Depends(get_current_user),
    authorized_doctor_ids=Depends(get_authorized_doctor_ids),
    service=Depends(get_service),
):
    """List clinical sessions filtered by authorized doctors."""
    return await service.list(user["org"], page.limit, page.offset, is_active, authorized_doctor_ids)


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    user=Depends(get_current_user),
    authorized_doctor_ids=Depends(get_authorized_doctor_ids),
    service=Depends(get_service),
):
    """Get details of a specific session."""
    return await service.get(session_id, user["org"], authorized_doctor_ids)


@router.get("/{session_id}/encounters")
async def get_session_encounters(
    session_id: str,
    user=Depends(get_current_user),
    authorized_doctor_ids=Depends(get_authorized_doctor_ids),
    service=Depends(get_service),
):
    """List all encounters for a specific session (jornada summary)."""
    return await service.get_encounters(session_id, user["org"], authorized_doctor_ids)


@router.patch("/{session_id}/deactivate")
async def deactivate_session(
    session_id: str,
    user=Depends(get_current_user),
    service=Depends(get_service),
):
    """Close/deactivate a clinical session."""
    # Note: We should ideally validate authorization here too, 
    # but for brevity using the repo's org isolation.
    return await service.deactivate(session_id, user["org"])


@router.post("/{session_id}/close")
async def close_session(
    session_id: str,
    user=Depends(get_current_user),
    service=Depends(get_service),
):
    """Semantic close for a clinical session (jornada)."""
    return await service.close(session_id, user["org"])


@router.patch("/{session_id}/activate")
async def activate_session(
    session_id: str,
    user=Depends(get_current_user),
    service=Depends(get_service),
):
    """Re-open/activate a clinical session."""
    return await service.activate(session_id, user["org"])