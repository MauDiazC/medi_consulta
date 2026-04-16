import logging
from google import genai
from app.core.config import settings
import asyncio

logger = logging.getLogger("rag.embeddings")

class EmbeddingService:
    """
    RAG Embedding Service using Google Gemini Embeddings (New SDK).
    Uses 'text-embedding-004' for clinical semantic search.
    """
    
    def __init__(self):
        if settings.get("GOOGLE_AI_API_KEY"):
            self.client = genai.Client(api_key=settings.GOOGLE_AI_API_KEY)
        else:
            self.client = None
            logger.warning("GOOGLE_AI_API_KEY not found. Embeddings will fail.")

    async def embed(self, text: str):
        """Generates semantic vectors for medical text."""
        if not self.client:
            raise RuntimeError("Google AI Client not configured.")

        try:
            # Execute embedding generation with new SDK
            result = await asyncio.to_thread(
                self.client.models.embed_content,
                model="text-embedding-004",
                contents=text,
                config=genai.types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT"
                )
            )
            
            # The new SDK returns embeddings in a slightly different structure
            return result.embeddings[0].values
            
        except Exception as e:
            logger.error(f"Gemini Embedding Error: {str(e)}")
            raise RuntimeError(f"Failed to generate clinical embeddings: {str(e)}")
