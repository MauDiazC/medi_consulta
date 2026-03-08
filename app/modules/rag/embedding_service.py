import httpx

from app.core.config import settings


class EmbeddingService:

    async def embed(self, text: str):

        async with httpx.AsyncClient() as client:

            r = await client.post(
                "https://api.groq.com/openai/v1/embeddings",
                headers={
                    "Authorization":
                    f"Bearer {settings.groq_api_key}"
                },
                json={
                    "model": "text-embedding-3-small",
                    "input": text,
                },
            )

        return r.json()["data"][0]["embedding"]
