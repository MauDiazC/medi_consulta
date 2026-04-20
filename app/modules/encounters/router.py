from fastapi import APIRouter, Depends
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user
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
    s=Depends(get_service),
):
    return await s.create(payload, user["org"], user["sub"])


@router.get("")
async def list_encounters(
    page=Depends(pagination_params),
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    return await s.list(user["org"], page.limit, page.offset)


@router.get("/patient/{patient_id}")
async def encounters_by_patient(
    patient_id: uuid.UUID,
    page=Depends(pagination_params),
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    return await s.list_by_patient(
        str(patient_id),
        user["org"],
        page.limit,
        page.offset,
    )


@router.get("/doctor/{doctor_id}")
async def encounters_by_doctor(
    doctor_id: uuid.UUID,
    page=Depends(pagination_params),
    user=Depends(get_current_user),
    s=Depends(get_service),
):
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
    s=Depends(get_service),
):
    return await s.list_by_session(
        str(session_id),
        user["org"],
        page.limit,
        page.offset,
    )


@router.get("/{encounter_id}")
async def get_encounter(
    encounter_id: uuid.UUID,
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    return await s.get(str(encounter_id), user["org"])


@router.put("/{encounter_id}")
async def update_encounter(
    encounter_id: uuid.UUID,
    payload: EncounterUpdate,
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    return await s.update(str(encounter_id), user["org"], payload)


@router.patch("/{encounter_id}/close")
async def close_encounter(
    encounter_id: uuid.UUID,
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    await s.close(str(encounter_id), user["org"])
    return {"status": "closed"}


@router.patch("/{encounter_id}/reassign/{new_doctor_id}")
async def reassign_encounter(
    encounter_id: uuid.UUID,
    new_doctor_id: uuid.UUID,
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    """
    Emergency endpoint to reassign an encounter to a different doctor.
    """
    return await s.reassign(str(encounter_id), user["org"], str(new_doctor_id))