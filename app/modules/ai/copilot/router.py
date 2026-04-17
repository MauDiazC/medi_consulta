from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from google import genai
from app.core.config import settings

from app.core.database import get_db
from app.core.permissions import require_role

from .repository import CopilotRepository
from .service import CopilotService

router = APIRouter(
    prefix="/copilot",
    tags=["copilot"],
)


def get_service(db: AsyncSession = Depends(get_db)):
    return CopilotService(
        CopilotRepository(db)
    )


@router.post("/analyze/{note_id}")
async def analyze_note(
    note_id: str,
    payload: dict,
    user=Depends(
        require_role("doctor")
    ),
    service=Depends(get_service),
):
    return await service.process_snapshot(
        note_id,
        payload["session_id"],
        payload,
    )


@router.get("/diag/models")
async def list_available_models(
    user=Depends(require_role("admin"))
):
    """
    Diagnostic endpoint to see which Gemini models are active for this API Key.
    Restricted to Super Admin (via email check).
    """
    if user.get("email") != "mdiazcabr@gmail.com":
        raise HTTPException(status_code=403, detail="Only global admins can access AI diagnostics.")
        
    api_key = settings.get("GOOGLE_AI_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_AI_API_KEY not found"}

    try:
        client = genai.Client(api_key=api_key)
        models = client.models.list()
        return {
            "api_key_fragment": f"{api_key[:5]}...",
            "models": [
                {"name": m.name, "methods": m.supported_methods} 
                for m in models
            ]
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/{note_id}")
async def get_suggestions(
    note_id: str,
    service=Depends(get_service),
):
    return await service.suggestions(note_id)
