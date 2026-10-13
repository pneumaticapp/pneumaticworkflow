"""Atomic rolling minute limits shared by every resource-server process."""

import hashlib
import secrets
from typing import Protocol

from redis.asyncio import Redis
from redis.backoff import NoBackoff
from redis.exceptions import RedisError
from redis.retry import Retry

from pneumatic_mcp.errors import CoreError

WINDOW_SECONDS = 60
CONNECTION_LIMIT = 60
ACCOUNT_LIMIT = 300

# Use Redis TIME rather than a replica's clock. Both budgets are checked and
# charged atomically; denied calls consume neither budget. The shared hash tag
# keeps these two keys in one slot if the deployment uses Redis Cluster.
LIMIT_SCRIPT = """
local clock = redis.call('TIME')
local now = tonumber(clock[1]) + tonumber(clock[2]) / 1000000
local cutoff = now - tonumber(ARGV[1])
for i = 1, 2 do
    redis.call('ZREMRANGEBYSCORE', KEYS[i], '-inf', cutoff)
end
for i = 1, 2 do
    if redis.call('ZCARD', KEYS[i]) >= tonumber(ARGV[i + 1]) then
        return 0
    end
end
for i = 1, 2 do
    redis.call('ZADD', KEYS[i], now, ARGV[4])
    redis.call('EXPIRE', KEYS[i], tonumber(ARGV[1]) + 1)
end
return 1
"""


class RateLimiter(Protocol):
    async def acquire(self, connection_id: str, account_id: int): ...
    async def close(self): ...


class RedisRateLimiter:
    def __init__(self, url: str, *, prefix: str = "pneumatic-mcp:v1"):
        self.prefix = prefix
        self.redis = Redis.from_url(
            url,
            socket_connect_timeout=2,
            socket_timeout=2,
            max_connections=64,
            retry_on_timeout=False,
            retry=Retry(backoff=NoBackoff(), retries=0),
        )

    async def acquire(self, connection_id: str, account_id: int):
        # Hash identity so Redis keys do not expose user/connection
        # identifiers.
        connection = hashlib.sha256(connection_id.encode()).hexdigest()
        account = hashlib.sha256(str(account_id).encode()).hexdigest()
        keys = [
            f"{self.prefix}:{{limits}}:connection:{connection}",
            f"{self.prefix}:{{limits}}:account:{account}",
        ]
        try:
            accepted = await self.redis.eval(
                LIMIT_SCRIPT,
                2,
                *keys,
                WINDOW_SECONDS,
                CONNECTION_LIMIT,
                ACCOUNT_LIMIT,
                secrets.token_hex(16),
            )
        except (RedisError, OSError, TimeoutError):
            raise CoreError(code="unavailable") from None
        if accepted != 1:
            raise CoreError(code="rate_limited", status=429)

    async def close(self):
        await self.redis.aclose()
