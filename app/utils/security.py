import logging

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
    if api_key not in settings.api_keys:
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key. Use X-API-Key with a valid key.",
        )
    user_id = settings.api_keys[api_key]
    logger.info(f"Authenticated User: {user_id}")
    return user_id
