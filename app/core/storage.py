import os
import logging
from app.core.config import settings

logger = logging.getLogger("core.storage")

# Defensive check: Cloudinary library crashes on import if CLOUDINARY_URL is malformed 
# (e.g. contains quotes or spaces from Railway/dotenv).
if os.environ.get("CLOUDINARY_URL"):
    # Clean the environment variable before the library reads it during 'import cloudinary'
    os.environ["CLOUDINARY_URL"] = os.environ["CLOUDINARY_URL"].strip().strip('"').strip("'")

import cloudinary
import cloudinary.uploader

# Configure Cloudinary
# Use CLOUDINARY_URL in your .env/Railway settings:
# CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
if settings.get("CLOUDINARY_URL"):
    cloudinary.config(secure=True)
else:
    logger.warning("CLOUDINARY_URL not found in settings. File uploads will fail.")

async def upload_image(file_content: bytes, folder: str = "mediconsulta") -> str | None:
...
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
