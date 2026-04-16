import logging
import google.generativeai as genai
from app.core.config import settings
import anyio

logger = logging.getLogger("rag.embeddings")

class EmbeddingService:
    """
    RAG Embedding Service using Google Gemini Embeddings.
    Uses 'models/text-embedding-004' for clinical semantic search.
    """
    
    def __init__(self):
        if settings.get("GOOGLE_AI_API_KEY"):
            genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
        else:
            logger.warning("GOOGLE_AI_API_KEY not found. Embeddings will fail.")

    async def embed(self, text: str):
        """Generates semantic vectors for medical text."""
        try:
            # Execute embedding generation
            result = await anyio.to_thread.run_sync(
                lambda: genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type="retrieval_document"
                )
            )
            return result['embedding']
            
        except Exception as e:
            logger.error(f"Gemini Embedding Error: {str(e)}")
            # En un sistema clínico no podemos retornar un vector vacío sin avisar
            raise RuntimeError(f"Failed to generate clinical embeddings: {str(e)}")
