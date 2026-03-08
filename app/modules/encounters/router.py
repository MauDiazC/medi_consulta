from fastapi import APIRouter, Depends

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
    patient_id: str,
    page=Depends(pagination_params),
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    return await s.list_by_patient(
        patient_id,
        user["org"],
        page.limit,
        page.offset,
    )


@router.get("/doctor/{doctor_id}")
async def encounters_by_doctor(
    doctor_id: str,
    page=Depends(pagination_params),
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    return await s.list_by_doctor(
        doctor_id,
        user["org"],
        page.limit,
        page.offset,
    )


@router.get("/session/{session_id}")
async def encounters_by_session(
    session_id: str,
    page=Depends(pagination_params),
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    return await s.list_by_session(
        session_id,
        user["org"],
        page.limit,
        page.offset,
    )


@router.get("/{encounter_id}")
async def get_encounter(
    encounter_id: str,
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    return await s.get(encounter_id, user["org"])


@router.put("/{encounter_id}")
async def update_encounter(
    encounter_id: str,
    payload: EncounterUpdate,
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    return await s.update(encounter_id, user["org"], payload)


@router.patch("/{encounter_id}/close")
async def close_encounter(
    encounter_id: str,
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    await s.close(encounter_id, user["org"])
    return {"status": "closed"}