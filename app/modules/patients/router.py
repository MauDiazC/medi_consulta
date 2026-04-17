from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.pagination import pagination_params
from app.core.permissions import require_role

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
    s=Depends(get_service)
):
    """Secure creation: Automatically link to user's organization."""
    return await s.create(payload, user["org"])


@router.get("")
async def list_patients(
    page=Depends(pagination_params),
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    """SaaS Guard: List only patients from your organization."""
    return await s.list(user["org"], page.limit, page.offset)


@router.get("/{patient_id}")
async def get_patient(
    patient_id: str,
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    """Secure fetch: Validate organization ownership."""
    patient = await s.get(patient_id, user["org"])
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return patient


@router.put("/{patient_id}")
async def update_patient(
    patient_id: str,
    payload: PatientUpdate,
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    """Secure update: Validate organization ownership."""
    return await s.update(patient_id, user["org"], payload)


@router.patch("/{patient_id}/deactivate")
async def deactivate_patient(
    patient_id: str,
    user=Depends(require_role("admin", "doctor")),
    s=Depends(get_service),
):
    """Soft delete: Restricted to clinical staff or admins."""
    await s.deactivate(patient_id, user["org"])
    return {"status": "deactivated"}


@router.patch("/{patient_id}/activate")
async def activate_patient(
    patient_id: str,
    user=Depends(require_role("admin", "doctor")),
    s=Depends(get_service),
):
    """Re-enables a patient profile."""
    # We need to implement activate in service/repo if not already there
    await s.repo.db.execute(
        text("UPDATE patients SET is_active=true WHERE id=CAST(:id AS UUID) AND organization_id=CAST(:org AS UUID)"),
        {"id": patient_id, "org": user["org"]}
    )
    await s.repo.db.commit()
    return {"status": "activated"}
