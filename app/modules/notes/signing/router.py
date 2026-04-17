from fastapi import APIRouter, Depends, File, UploadFile, Header, HTTPException, Body, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_role
from app.core.pagination import pagination_params
from app.modules.notes.signing.service import SigningApplicationService
from app.modules.notes.repository import ClinicalNoteRepository
from app.modules.notes.signing.models import NoteSnapshot
from app.modules.notes.signing.identity_repository import ProfessionalIdentityRepository
from app.modules.notes.signing.schemas import ProfessionalIdentitySetup

router = APIRouter(prefix="/notes/signing", tags=["signing"])

@router.post("/professional-identity")
async def setup_professional_identity(
    payload: ProfessionalIdentitySetup,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Physician Onboarding: Register public key and license.
    Ensures future signatures can be verified without re-uploading keys.
    """
    repo = ProfessionalIdentityRepository(db)
    await repo.register(
        user_id=user["sub"],
        org_id=user["org"],
        public_key_pem=payload.public_key_pem,
        license_number=payload.license_number,
        specialty=payload.specialty
    )
    return {"message": "Professional identity successfully registered."}

@router.post("/professional-identity/upload")
async def upload_professional_identity(
    license_number: str = Form(...),
    specialty: Optional[str] = Form(None),
    public_key_file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Physician Onboarding via File Upload.
    Allows uploading the .pem public key directly.
    """
    public_pem = (await public_key_file.read()).decode()
    
    repo = ProfessionalIdentityRepository(db)
    await repo.register(
        user_id=user["sub"],
        org_id=user["org"],
        public_key_pem=public_pem,
        license_number=license_number,
        specialty=specialty
    )
    return {"message": "Professional identity file successfully registered."}

@router.get("/professional-identity")
async def list_identities(
    page=Depends(pagination_params),
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Admin only: List all professional identities in the organization."""
    repo = ProfessionalIdentityRepository(db)
    return await repo.list_by_org(user["org"], page.limit, page.offset)

@router.get("/professional-identity/me")
async def get_my_identity(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Checks the current registration of professional metadata."""
    repo = ProfessionalIdentityRepository(db)
    identity = await repo.get_by_user(user["sub"], user["org"])
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found. Please register first.")
    return identity

# --- Administrative Identity Management ---

@router.patch("/professional-identity/{user_id}/deactivate")
async def deactivate_user_identity(
    user_id: str,
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Admin only: Revokes the professional identity of a specific user in the org."""
    repo = ProfessionalIdentityRepository(db)
    updated = await repo.deactivate(user_id, user["org"])
    if not updated:
        raise HTTPException(
            status_code=404, 
            detail="Professional identity not found for this user in your organization."
        )
    return {"status": "deactivated", "user_id": user_id}

@router.patch("/professional-identity/{user_id}/activate")
async def activate_user_identity(
    user_id: str,
    user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Admin only: Re-enables the professional identity of a specific user in the org."""
    repo = ProfessionalIdentityRepository(db)
    updated = await repo.activate(user_id, user["org"])
    if not updated:
        raise HTTPException(
            status_code=404, 
            detail="Professional identity not found for this user in your organization."
        )
    return {"status": "activated", "user_id": user_id}

# --- Personal Identity Management ---

@router.patch("/professional-identity/me/deactivate")
async def deactivate_my_identity(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """User only: Revokes their own identity (Emergency)."""
    repo = ProfessionalIdentityRepository(db)
    await repo.deactivate(user["sub"], user["org"])
    return {"status": "deactivated"}

@router.patch("/professional-identity/me/activate")
async def activate_my_identity(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """User only: Re-enables their own identity."""
    repo = ProfessionalIdentityRepository(db)
    await repo.activate(user["sub"], user["org"])
    return {"status": "activated"}


@router.post("/sign/{note_id}")
async def sign_note_endpoint(
    note_id: str,
    x_idempotency_key: str = Header(None),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ClinicalNoteRepository(db)
    # Validate organization isolation
    note = await repo.get(note_id, user["org"])
    if not note:
        raise HTTPException(404, "Note not found")

    signing_app = SigningApplicationService(db)
    return await signing_app.execute_signing(
        note=note,
        version=note, # Current architecture returns note as dict with version
        signer_id=user["sub"],
        idempotency_key=x_idempotency_key
    )

@router.get("/snapshot/{snapshot_id}")
async def get_snapshot_endpoint(
    snapshot_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    snapshot = await db.get(NoteSnapshot, snapshot_id)
    if not snapshot:
        raise HTTPException(404, "Snapshot not found")
    return snapshot

@router.post("/seal/{encounter_id}")
async def seal_encounter_endpoint(
    encounter_id: str,
    x_idempotency_key: str = Header(None),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    signing_app = SigningApplicationService(db)
    return await signing_app.execute_encounter_sealing(
        encounter_id=encounter_id,
        signer_id=user["sub"],
        idempotency_key=x_idempotency_key
    )
