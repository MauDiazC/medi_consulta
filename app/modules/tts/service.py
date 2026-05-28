import logging
from collections.abc import AsyncIterator

from elevenlabs.client import AsyncElevenLabs
from fastapi import HTTPException

from app.core.config import settings

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
        Initializes the connection and retrieves the first chunk before returning
        to ensure any errors (auth, quota, etc.) are caught and raised before the
        HTTP response headers are sent.
        """
        if not self.client:
            raise HTTPException(
                status_code=503, detail="Servicio de voz no configurado."
            )

        try:
            audio_stream = self.client.text_to_speech.stream(
                text=text, voice_id=self.voice_id, model_id="eleven_multilingual_v2"
            )
            # Try to get the first chunk to verify the stream starts successfully.
            # This will raise ApiError immediately if authentication or quota fails.
            first_chunk = await anext(audio_stream, None)
        except Exception as e:
            logger.error(f"Error al iniciar stream en TTSService: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error ElevenLabs: {str(e)}") from e

        async def _generator() -> AsyncIterator[bytes]:
            if first_chunk:
                yield first_chunk
            try:
                async for chunk in audio_stream:
                    if chunk:
                        yield chunk
                logger.info("Generación de audio completada exitosamente.")
            except Exception as e:
                logger.error(f"Error en TTSService durante la transmisión: {str(e)}", exc_info=True)

        return _generator()

    async def speak_prescription(self, plan_text: str) -> AsyncIterator[bytes]:
        intro = (
            "Estimado paciente, a continuación escuchará su plan de cuidado y receta médica "
            "proporcionada por su especialista. Por favor, preste atención: "
        )
        full_text = f"{intro} {plan_text}"
        return await self.generate_speech_stream(full_text)

