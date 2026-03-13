from fastapi import APIRouter, Depends, File, UploadFile, Header, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.notes.signing.service import SigningApplicationService
from app.modules.notes.repository import ClinicalNoteRepository

router = APIRouter(prefix="/notes/signing", tags=["signing"])

@router.post("/sign/{note_id}")
async def sign_note_endpoint(
    note_id: str,
    x_idempotency_key: str = Header(None),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note, version = await ClinicalNoteRepository(db).get_note_and_version(note_id)
    if not note:
        raise HTTPException(404, "Note not found")

    signing_app = SigningApplicationService(db)
    return await signing_app.execute_signing(
        note=note,
        version=version,
        signer_id=user["sub"],
        idempotency_key=x_idempotency_key
    )

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

@router.post("/keys/rotate")
async def rotate_keys_endpoint(
    public_key: str = Body(...),
    private_key: str = Body(...),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    signing_app = SigningApplicationService(db)
    return await signing_app.rotate_organization_key(
        organization_id=user["org"],
        public_key_pem=public_key,
        private_key_pem=private_key,
        executor_id=user["sub"]
    )

@router.post("/keys/upload")
async def upload_keys_endpoint(
    public_key_file: UploadFile = File(...),
    private_key_file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    public_pem = (await public_key_file.read()).decode()
    private_pem = (await private_key_file.read()).decode()

    signing_app = SigningApplicationService(db)
    return await signing_app.rotate_organization_key(
        organization_id=user["org"],
        public_key_pem=public_pem,
        private_key_pem=private_pem,
        executor_id=user["sub"]
    )
