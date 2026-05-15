import os
import logging
from app.core.config import settings

logger = logging.getLogger("core.storage")

# Defensive Hack: Cloudinary library auto-initializes on 'import' by reading CLOUDINARY_URL.
# If the URL has any formatting issues (quotes, spaces), it raises ValueError and crashes the app.
_actual_cloudinary_url = os.environ.get("CLOUDINARY_URL")
if _actual_cloudinary_url:
    # Temporarily remove it so 'import cloudinary' doesn't crash
    os.environ.pop("CLOUDINARY_URL", None)

import cloudinary
import cloudinary.uploader

# Manual Configuration
if _actual_cloudinary_url:
    try:
        clean_url = _actual_cloudinary_url.strip().strip('"').strip("'")
        if not clean_url.startswith("cloudinary://"):
            # If the user forgot the prefix, we add it to be helpful
            clean_url = f"cloudinary://{clean_url}"
        
        cloudinary.config_from_url(clean_url)
        cloudinary.config(secure=True)
        logger.info("Cloudinary configured successfully via manual URL injection.")
    except Exception as e:
        logger.error(f"Failed to configure Cloudinary manually: {str(e)}")
else:
    logger.warning("CLOUDINARY_URL not found. File uploads will be disabled.")

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
