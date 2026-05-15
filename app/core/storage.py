import cloudinary
import cloudinary.uploader
from app.core.config import settings
import logging

logger = logging.getLogger("core.storage")

# Configure Cloudinary
# Use CLOUDINARY_URL in your .env/Railway settings:
# CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
if settings.get("CLOUDINARY_URL"):
    cloudinary.config(secure=True)
else:
    logger.warning("CLOUDINARY_URL not found in settings. File uploads will fail.")

async def upload_image(file_content: bytes, folder: str = "mediconsulta") -> str | None:
    """
    Uploads a raw bytes image to Cloudinary and returns the secure URL.
    """
    try:
        # We use asyncio.to_thread because the cloudinary SDK is synchronous
        import asyncio
        result = await asyncio.to_thread(
            cloudinary.uploader.upload,
            file_content,
            folder=folder,
            resource_type="image"
        )
        return result.get("secure_url")
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {str(e)}")
        return None
