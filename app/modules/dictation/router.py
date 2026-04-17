from fastapi import APIRouter, Depends, Body, UploadFile, File
from app.core.dependencies import get_current_user
from app.core.permissions import require_role
from .soap_classifier import SOAPClassifier
from .speech_service import SpeechService

router = APIRouter(prefix="/dictation", tags=["dictation"])

def get_speech_service():
    return SpeechService()

@router.post("/transcribe")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    user=Depends(require_role("doctor")),
    s: SpeechService = Depends(get_speech_service)
):
    """
    Toma un archivo de audio médico y lo convierte a texto.
    Solo disponible para Doctores.
    """
    content = await audio_file.read()
    text = await s.transcribe(content)
    return {"text": text}

@router.post("/classify")
async def classify_dictation(
    payload: dict = Body(...),
    user=Depends(require_role("doctor"))
):
    """
    Toma un texto libre (dictado) y lo organiza en secciones SOAP usando IA (Google Gemini).
    """
    text = payload.get("text")
    classifier = SOAPClassifier()
    return await classifier.classify(text)
