import google.generativeai as genai
from app.core.config import settings
from .base import SpeechProvider
import logging
import anyio

logger = logging.getLogger("dictation.google")

class GoogleSpeechProvider(SpeechProvider):
    """
    STT Provider using Google Gemini 1.5 Flash.
    Uses multimodal capabilities to transcribe audio.
    """
    
    def __init__(self):
        if settings.get("GOOGLE_AI_API_KEY"):
            genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            logger.warning("GOOGLE_AI_API_KEY not found. STT will be disabled.")

    async def transcribe_chunk(self, audio: bytes) -> str:
        """
        Multimodal transcription using Gemini.
        """
        if not self.model:
            return ""

        try:
            # Prepare audio part
            audio_part = {
                "mime_type": "audio/wav",
                "data": audio
            }
            
            prompt = "Transcribe exactamente lo que se dice en este audio médico. No añadidas nada más."
            
            # Execute in thread to avoid blocking if the SDK is not fully async friendly
            response = await anyio.to_thread.run_sync(
                lambda: self.model.generate_content([prompt, audio_part])
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini STT Error: {str(e)}")
            return ""
