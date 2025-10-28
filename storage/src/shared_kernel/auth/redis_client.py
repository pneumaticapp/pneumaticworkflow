import pickle
from typing import Any

import redis.asyncio as redis

from src.shared_kernel.config import get_settings
from src.shared_kernel.exceptions import (
    MSG_EXT_011,
    MSG_EXT_012,
    MSG_EXT_013,
    RedisConnectionError,
    RedisOperationError,
)


class RedisAuthClient:
    def __init__(self, redis_url: str) -> None:
        # Settings match Django: KEY_PREFIX = '' for auth cache
        self._client = redis.from_url(redis_url)

    async def get(self, key: str) -> dict[str, Any] | None:
        """Get value from cache"""
        try:
            settings = get_settings()
            value = await self._client.get(f'{settings.KEY_PREFIX_REDIS}{key}')
            if value is None:
                return None
            # Note: pickle.loads can be unsafe with untrusted data
            # In production, consider using a safer serialization method
            return pickle.loads(value)  # noqa: S301
        except redis.ConnectionError as e:
            raise RedisConnectionError(
                details=MSG_EXT_011.format(details=str(e)),
            ) from e
        except redis.RedisError as e:
            raise RedisOperationError(
                operation='get',
                details=MSG_EXT_012.format(key=key, details=str(e)),
            ) from e
        except pickle.UnpicklingError as e:
            raise RedisOperationError(
                operation='unpickle',
                details=MSG_EXT_013.format(key=key, details=str(e)),
            ) from e


def get_redis_client() -> RedisAuthClient:
    """Get or create Redis client"""
    settings = get_settings()
    return RedisAuthClient(settings.AUTH_REDIS_URL)
