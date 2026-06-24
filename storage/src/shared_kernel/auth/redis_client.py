"""Redis client for authentication."""

import builtins
import io
import pickle
from functools import lru_cache
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

# Types that Django's django_redis PickleSerializer can produce
# for PneumaticToken auth data (dict, list, str, int, bool, None).
_SAFE_BUILTINS = frozenset(
    {
        'dict',
        'list',
        'set',
        'frozenset',
        'tuple',
        'str',
        'bytes',
        'int',
        'float',
        'bool',
    }
)


class _RestrictedUnpickler(pickle.Unpickler):
    """Unpickler that blocks arbitrary code execution.

    Only allows instantiation of safe built-in types.
    Rejects any class with __reduce__-based RCE payloads
    (os.system, subprocess, exec, eval, etc.).

    Compatible with django_redis PickleSerializer output.
    """

    def find_class(self, module: str, name: str) -> type:
        if module == 'builtins' and name in _SAFE_BUILTINS:
            return getattr(builtins, name)
        msg = f'Unsafe class blocked: {module}.{name}'
        raise pickle.UnpicklingError(msg)


def _safe_loads(data: bytes) -> Any:  # noqa: ANN401
    """Deserialize pickle data using RestrictedUnpickler."""
    return _RestrictedUnpickler(io.BytesIO(data)).load()


def _validate_auth_data(data: Any) -> dict[str, Any] | list[str] | None:  # noqa: ANN401
    """Validate deserialized auth data matches expected structure.

    Django PneumaticToken stores two types of values:
    - encrypted_token → dict with user_id, account_id, etc.
    - user_pk → list of encrypted token strings

    Returns validated data or None if structure is invalid.
    """
    # Token data: dict with user_id key (regular token)
    # or dict with account_id key only (public/embed token)
    if isinstance(data, dict):
        if 'user_id' not in data and 'account_id' not in data:
            return None
        return data

    # User token list: list of token hex strings
    if isinstance(data, list) and all(isinstance(item, str) for item in data):
        return data
    return None


class RedisAuthClient:
    """Redis client for authentication operations."""

    def __init__(self, redis_url: str) -> None:
        """Initialize Redis client.

        Args:
            redis_url: Redis connection URL.

        """
        # Settings match Django: KEY_PREFIX = '' for auth cache
        self._client = redis.from_url(redis_url)  # type: ignore[no-untyped-call]

    async def get(self, key: str) -> dict[str, Any] | list[str] | None:
        """Get value from cache."""
        try:
            settings = get_settings()
            value = await self._client.get(f'{settings.KEY_PREFIX_REDIS}{key}')
            if value is None:
                return None
            deserialized = _safe_loads(value)
            return _validate_auth_data(deserialized)
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

    async def close(self) -> None:
        """Close Redis connection pool."""
        await self._client.aclose()


@lru_cache
def get_redis_client() -> RedisAuthClient:
    """Get or create Redis client singleton.

    Uses @lru_cache to return the same instance across calls,
    matching the get_settings() pattern.
    """
    settings = get_settings()
    return RedisAuthClient(settings.AUTH_REDIS_URL)


async def close_redis_client() -> None:
    """Close Redis client and clear cache for shutdown."""
    try:
        client = get_redis_client()
        await client.close()
    finally:
        get_redis_client.cache_clear()
