from arq.connections import RedisSettings
from app.core.config import settings

# Parse connection params from REDIS_URL if needed, 
# but ARQ can take a URL directly in some versions or RedisSettings.
# Railway gives us a URL like redis://default:pass@host:port

def get_redis_settings() -> RedisSettings:
    """
    Extracts settings from REDIS_URL for ARQ.
    """
    from urllib.parse import urlparse
    url = urlparse(settings.REDIS_URL)
    return RedisSettings(
        host=url.hostname or "localhost",
        port=url.port or 6379,
        password=url.password,
        database=0, # Default
        conn_timeout=10,
    )
