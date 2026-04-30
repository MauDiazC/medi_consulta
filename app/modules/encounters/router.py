from fastapi import APIRouter, Depends, HTTPException
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_authorized_doctor_ids
from app.core.pagination import pagination_params

from .repository import EncounterRepository
from .schemas import EncounterCreate, EncounterUpdate
from .service import EncounterService

router = APIRouter(prefix="/encounters", tags=["encounters"])


def get_service(db=Depends(get_db)):
    return EncounterService(EncounterRepository(db))


@router.post("")
async def create_encounter(
    payload: EncounterCreate,
    user=Depends(get_current_user),
    authorized_doctor_ids=Depends(get_authorized_doctor_ids),
    s=Depends(get_service),
):
    # Security: Ensure the user is authorized to create for this doctor
    if str(payload.doctor_id) not in authorized_doctor_ids:
        raise HTTPException(403, "Not authorized to create encounters for this doctor")
        
    return await s.create(payload, user["org"], str(payload.doctor_id))


@router.get("")
async def list_encounters(
    page=Depends(pagination_params),
    user=Depends(get_current_user),
    authorized_doctor_ids=Depends(get_authorized_doctor_ids),
    s=Depends(get_service),
):
    """Lists encounters filtered by authorized doctors."""
    return await s.list(user["org"], page.limit, page.offset, authorized_doctor_ids)


@router.get("/patient/{patient_id}")
async def encounters_by_patient(
    patient_id: uuid.UUID,
    page=Depends(pagination_params),
    user=Depends(get_current_user),
    authorized_doctor_ids=Depends(get_authorized_doctor_ids),
    s=Depends(get_service),
):
    """Lists patient encounters filtered by authorized doctors."""
    return await s.list_by_patient(
        str(patient_id),
        user["org"],
        page.limit,
        page.offset,
        authorized_doctor_ids
    )


@router.get("/doctor/{doctor_id}")
async def encounters_by_doctor(
    doctor_id: uuid.UUID,
    page=Depends(pagination_params),
    user=Depends(get_current_user),
    authorized_doctor_ids=Depends(get_authorized_doctor_ids),
    s=Depends(get_service),
):
    """Lists encounters for a specific doctor, if authorized."""
    if str(doctor_id) not in authorized_doctor_ids:
        raise HTTPException(403, "Not authorized to view encounters for this doctor")
        
    return await s.list_by_doctor(
        str(doctor_id),
        user["org"],
        page.limit,
        page.offset,
    )


@router.get("/session/{session_id}")
async def encounters_by_session(
    session_id: uuid.UUID,
    page=Depends(pagination_params),
    user=Depends(get_current_user),
    authorized_doctor_ids=Depends(get_authorized_doctor_ids),
    s=Depends(get_service),
):
    """Lists encounters for a session filtered by authorized doctors."""
    return await s.list_by_session(
        str(session_id),
        user["org"],
        page.limit,
        page.offset,
        authorized_doctor_ids
    )
