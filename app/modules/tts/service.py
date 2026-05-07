import logging
from typing import AsyncIterator
from elevenlabs.client import AsyncElevenLabs
from app.core.config import settings
from fastapi import HTTPException

logger = logging.getLogger("modules.tts")

class TTSService:
    """
    Professional TTS Service using ElevenLabs.
    """
    
    def __init__(self):
        self.api_key = settings.get("ELEVENLABS_API_KEY")
        self.voice_id = settings.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        
        if not self.api_key or self.api_key == "dummy-eleven-key":
            self.client = None
            logger.warning("ElevenLabs API Key not configured.")
        else:
            self.client = AsyncElevenLabs(api_key=self.api_key)

    async def generate_speech_stream(self, text: str) -> AsyncIterator[bytes]:
        """
        Generates a streaming audio response from text.
        """
        if not self.client:
            raise HTTPException(status_code=503, detail="Servicio de voz no configurado.")

        try:
            # DEBUG: Inspección de métodos reales en el entorno
            tts_client = self.client.text_to_speech
            logger.info(f"Atributos disponibles en TTS: {[m for m in dir(tts_client) if not m.startswith('_')]}")

            # Intentamos el método 'convert' que es el más común
            # En algunas versiones asíncronas, esto retorna un generador
            result = await tts_client.convert(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_multilingual_v2"
            )

            # Si el resultado es directamente bytes
            if isinstance(result, bytes):
                yield result
            # Si es un generador asíncrono
            else:
                async for chunk in result:
                    if chunk:
                        yield chunk
                    
            logger.info("Generación de audio completada.")
                
        except Exception as e:
            logger.error(f"Error en TTSService: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error ElevenLabs: {str(e)}")

    async def speak_prescription(self, plan_text: str) -> AsyncIterator[bytes]:
        intro = (
            "Estimado paciente, a continuación escuchará su plan de cuidado y receta médica "
            "proporcionada por su especialista. Por favor, preste atención: "
        )
        full_text = f"{intro} {plan_text}"
        async for chunk in self.generate_speech_stream(full_text):
            yield chunk
