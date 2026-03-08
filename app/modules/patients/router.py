from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.pagination import pagination_params

from .repository import PatientRepository
from .schemas import PatientCreate, PatientUpdate
from .service import PatientService

router = APIRouter(prefix="/patients", tags=["patients"])


def get_service(db=Depends(get_db)):
    return PatientService(PatientRepository(db))


@router.post("")
async def create_patient(
    payload: PatientCreate,
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    return await s.create(payload, user["org"])


@router.get("")
async def list_patients(
    page=Depends(pagination_params),
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    return await s.list(user["org"], page.limit, page.offset)


@router.get("/{patient_id}")
async def get_patient(
    patient_id: str,
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    return await s.get(patient_id, user["org"])


@router.put("/{patient_id}")
async def update_patient(
    patient_id: str,
    payload: PatientUpdate,
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    return await s.update(patient_id, user["org"], payload)


@router.patch("/{patient_id}/deactivate")
async def deactivate_patient(
    patient_id: str,
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    await s.deactivate(patient_id, user["org"])
    return {"status": "deactivated"}