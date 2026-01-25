"""Token authentication classes."""

import hashlib
from typing import Any

from src.shared_kernel.auth.redis_client import get_redis_client
from src.shared_kernel.config import get_settings


class PneumaticToken:
    """PneumaticToken implementation for FastAPI microservice.

    Based on Django implementation with Redis cache.
    """

    def __init__(self, key: str) -> None:
        """Initialize PneumaticToken.

        Args:
            key: Token key for encryption.

        """
        self.key = key

    @classmethod
    async def encrypt(cls, token: str) -> str:
        """Encrypt token using PBKDF2."""
        settings = get_settings()
        encrypted_token = hashlib.pbkdf2_hmac(
            'sha256',
            token.encode(),
            settings.DJANGO_SECRET_KEY.encode(),
            settings.AUTH_TOKEN_ITERATIONS,
        )
        return encrypted_token.hex()

    @classmethod
    async def data(cls, token: str) -> dict[str, Any] | None:
        """Get cached token data."""
        try:
            encrypted_token = await cls.encrypt(token)
            redis_client = get_redis_client()
            return await redis_client.get(encrypted_token)
        except (ValueError, KeyError, TypeError):
            # Handle specific token/redis errors
            return None
