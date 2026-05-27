import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.dependencies import get_current_user
from app.core.storage import upload_image

logger = logging.getLogger("modules.files.router")

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), user=Depends(get_current_user)):
    """
    Generic image upload endpoint.
    Returns the public URL from Cloudinary.
    The frontend should then save this URL in the profile/org settings.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Only images are allowed")

    content = await file.read()

    # Determine folder based on context (optional, let's keep it simple)
    url = await upload_image(content, folder=f"mediconsulta/org_{user['org']}")

    if not url:
        raise HTTPException(500, "Upload to cloud storage failed")

    return {"url": url}
