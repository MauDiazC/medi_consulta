import logging
from typing import AsyncIterator
from elevenlabs.client import AsyncElevenLabs
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
        self.voice_id = settings.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        
        if not self.api_key or self.api_key == "dummy-eleven-key":
            self.client = None
            logger.warning("ElevenLabs API Key not configured.")
        else:
            # En v1.0+, AsyncElevenLabs es el cliente recomendado
            self.client = AsyncElevenLabs(api_key=self.api_key)

    async def generate_speech_stream(self, text: str) -> AsyncIterator[bytes]:
        """
        Generates a streaming audio response from text.
        """
        if not self.client:
            logger.error("TTS Attempted but client is NOT configured.")
            raise HTTPException(status_code=503, detail="Servicio de voz no configurado.")

        try:
            logger.info(f"Iniciando generación TTS: {len(text)} caracteres")
            
            # En la versión 1.50+, el método más robusto suele ser .generate() directamente en el cliente
            # o .text_to_speech.convert()
            audio_stream = await self.client.generate(
                text=text,
                voice=self.voice_id,
                model="eleven_multilingual_v2",
                stream=True
            )
            
            async for chunk in audio_stream:
                if chunk:
                    yield chunk
                    
            logger.info("TTS Stream finalizado con éxito.")
                
        except Exception as e:
            logger.error(f"Error crítico en ElevenLabs: {str(e)}", exc_info=True)
            # No podemos lanzar HTTPException aquí si el yield ya empezó, 
            # pero este bloque capturará errores de inicialización.
            raise HTTPException(status_code=500, detail=f"Error ElevenLabs: {str(e)}")

    async def speak_prescription(self, plan_text: str) -> AsyncIterator[bytes]:
        intro = (
            "Estimado paciente, a continuación escuchará su plan de cuidado y receta médica "
            "proporcionada por su especialista. Por favor, preste atención: "
        )
        full_text = f"{intro} {plan_text}"
        async for chunk in self.generate_speech_stream(full_text):
            yield chunk
