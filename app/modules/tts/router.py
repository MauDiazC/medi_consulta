from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import StreamingResponse
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.notes.repository import ClinicalNoteRepository
from .service import TTSService
import uuid

router = APIRouter(prefix="/tts", tags=["tts"])

def get_service():
    return TTSService()

@router.get("/read-prescription/{note_id}")
async def read_prescription(
    note_id: uuid.UUID,
    db = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    s: TTSService = Depends(get_service)
):
    """
    Fetches the 'plan' section of a clinical note and converts it to audio.
    Only authorized personnel can request this.
    """
    # 1. Fetch note
    repo = ClinicalNoteRepository(db)
    note = await repo.get(str(note_id))

    if not note:
        raise HTTPException(status_code=404, detail="Nota clínica no encontrada.")
...
    plan_text = note.get("plan")
    if not plan_text:
        raise HTTPException(status_code=400, detail="La nota no contiene un plan o receta para leer.")

    # 2. Return streaming audio
    return StreamingResponse(
        s.speak_prescription(plan_text),
        media_type="audio/mpeg"
    )

@router.post("/read-text")
async def read_custom_text(
    payload: dict,
    current_user: dict = Depends(get_current_user),
    s: TTSService = Depends(get_service)
):
    """
    Converts any custom text to audio.
    Useful for immediate instructions not yet saved in a note.
    """
    text = payload.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="El texto es requerido.")
        
    return StreamingResponse(
        s.generate_speech_stream(text),
        media_type="audio/mpeg"
    )
