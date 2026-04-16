from fastapi import APIRouter, Depends, Body
from app.core.dependencies import get_current_user
from .soap_classifier import SOAPClassifier

router = APIRouter(prefix="/dictation", tags=["dictation"])

@router.post("/classify")
async def classify_dictation(
    payload: dict = Body(...),
    user=Depends(get_current_user)
):
    """
    Toma un texto libre (dictado) y lo organiza en secciones SOAP usando IA (Google Gemini).
    """
    text = payload.get("text")
    classifier = SOAPClassifier()
    return await classifier.classify(text)
