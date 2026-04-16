import logging
from typing import AsyncIterator
from elevenlabs import AsyncElevenLabs
from app.core.config import settings
from fastapi import HTTPException

logger = logging.getLogger("modules.tts")

class TTSService:
    """
    Professional TTS Service using ElevenLabs.
    Designed for clinical environment clarity and empathy.
    """
    
    def __init__(self):
        self.api_key = settings.get("ELEVENLABS_API_KEY")
        self.voice_id = settings.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM") # Default voice
        
        if not self.api_key or self.api_key == "dummy-eleven-key":
            self.client = None
            logger.warning("ElevenLabs API Key not configured. TTS will be disabled.")
        else:
            self.client = AsyncElevenLabs(api_key=self.api_key)

    async def generate_speech_stream(self, text: str) -> AsyncIterator[bytes]:
        """
        Generates a streaming audio response from text.
        """
        if not self.client:
            raise HTTPException(
                status_code=503, 
                detail="Servicio de voz no configurado en el servidor."
            )

        try:
            # ElevenLabs async stream
            audio_stream = await self.client.generate(
                text=text,
                voice=self.voice_id,
                model="eleven_multilingual_v2",
                stream=True
            )
            
            async for chunk in audio_stream:
                yield chunk
                
        except Exception as e:
            logger.error(f"ElevenLabs TTS Error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generando el audio de la receta: {str(e)}"
            )

    async def speak_prescription(self, plan_text: str) -> AsyncIterator[bytes]:
        """
        Prepares and speaks a clinical plan/prescription.
        Includes a professional intro for the patient.
        """
        intro = (
            "Estimado paciente, a continuación escuchará su plan de cuidado y receta médica "
            "proporcionada por su especialista en Mediconsulta. Por favor, preste atención a las "
            "siguientes indicaciones: "
        )
        full_text = f"{intro} {plan_text}"
        
        async for chunk in self.generate_speech_stream(full_text):
            yield chunk
