from google import genai
from app.core.config import settings
from .base import SpeechProvider
import logging
import asyncio

logger = logging.getLogger("dictation.google")

class GoogleSpeechProvider(SpeechProvider):
    """
    STT Provider using Google Gemini (New SDK).
    Uses multimodal capabilities to transcribe audio.
    """
    
    def __init__(self):
        if settings.get("GOOGLE_AI_API_KEY"):
            self.client = genai.Client(api_key=settings.GOOGLE_AI_API_KEY)
        else:
            self.client = None
            logger.warning("GOOGLE_AI_API_KEY not found. STT will be disabled.")

    async def transcribe_chunk(self, audio: bytes) -> str:
        """
        Multimodal transcription using Gemini.
        """
        if not self.client:
            return ""

        try:
            prompt = "Transcribe exactamente lo que se dice en este audio médico. No añadas nada más."
            
            # Using the latest stable model identifier
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model='gemini-2.0-flash',
                contents=[
                    prompt,
                    genai.types.Part.from_bytes(data=audio, mime_type="audio/wav")
                ]
            )
            
            if not response.text:
                logger.warning("Gemini returned empty text for audio.")
                return ""
                
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini STT Error: {str(e)}")
            return ""
