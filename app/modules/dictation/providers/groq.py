import httpx

from app.core.config import settings

from .base import SpeechProvider


class GroqSpeechProvider(SpeechProvider):

    async def transcribe_chunk(
        self,
        audio: bytes,
    ) -> str:

        async with httpx.AsyncClient() as client:

            files = {
                "file": ("audio.wav", audio),
                "model": (None, "whisper-large-v3"),
            }

            headers = {
                "Authorization":
                f"Bearer {settings.groq_api_key}"
            }

            r = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers=headers,
                files=files,
                timeout=30,
            )

            data = r.json()

            return data.get("text", "")
