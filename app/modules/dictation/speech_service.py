import logging
from .providers.google import GoogleSpeechProvider

logger = logging.getLogger("dictation.speech_service")

class SpeechService:
    def __init__(self):
        self.provider = GoogleSpeechProvider()

    async def transcribe(self, audio_data: bytes) -> str:
        """
        Transcribes medical audio data to text using the configured provider.
        """
        try:
            return await self.provider.transcribe_chunk(audio_data)
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return ""
