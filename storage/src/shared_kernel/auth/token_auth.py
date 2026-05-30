"""Token authentication classes."""

import hashlib
from functools import lru_cache
from typing import Any

from src.shared_kernel.auth.redis_client import get_redis_client
from src.shared_kernel.config import get_settings

# Threshold: below this, PBKDF2 runs inline (< 1ms).
# Above this, it would need asyncio.to_thread to avoid
# blocking the event loop (not currently needed since
# AUTH_TOKEN_ITERATIONS defaults to 1).
_INLINE_ITERATIONS_THRESHOLD = 100


@lru_cache(maxsize=256)
def _compute_pbkdf2(
    token: str,
    salt: str,
    iterations: int,
) -> str:
    """Compute PBKDF2-HMAC-SHA256 with LRU cache.

    Caches token→hash mappings to avoid re-hashing the same
    token on every request. Cache is bounded to 256 entries
    (evicts least-recently-used).

    Args:
        token: Raw token string.
        salt: Secret key for PBKDF2.
        iterations: Number of PBKDF2 iterations.

    Returns:
        Hex-encoded hash string.

    """
    return hashlib.pbkdf2_hmac(
        'sha256',
        token.encode(),
        salt.encode(),
        iterations,
    ).hex()


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
        """Encrypt token using PBKDF2.

        Uses inline computation (no thread) when iterations
        are below threshold. Results are cached via LRU.
        """
        settings = get_settings()
        return _compute_pbkdf2(
            token=token,
            salt=settings.DJANGO_SECRET_KEY,
            iterations=settings.AUTH_TOKEN_ITERATIONS,
        )

    @classmethod
    async def data(
        cls,
        token: str,
    ) -> dict[str, Any] | None:
        """Get cached token data."""
        try:
            encrypted_token = await cls.encrypt(token)
            redis_client = get_redis_client()
            data = await redis_client.get(encrypted_token)
            return data if isinstance(data, dict) else None
        except (ValueError, KeyError, TypeError):
            return None
