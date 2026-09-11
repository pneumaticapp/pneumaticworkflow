"""Writer of the audit journal: XADD into the Redis stream."""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from functools import lru_cache

import redis.asyncio as redis

from src.shared_kernel.config import get_settings
from src.shared_kernel.events.schema import STREAM_KEY, Event

logger = logging.getLogger(__name__)

CONNECT_TIMEOUT = 1
SOCKET_TIMEOUT = 2
EMIT_TIMEOUT = 3.0
CIRCUIT_OPEN_SECONDS = 15.0


def _now() -> float:
    # Module-level clock: the tests patch it instead of time.monotonic,
    # which the event loop itself relies on.
    return time.monotonic()


@dataclass
class StreamCircuit:
    """Circuit breaker of the write path, one per process."""

    open_until: float = 0.0
    dropped: int = 0

    def is_open(self, now: float) -> bool:
        """Whether writes are being dropped at this moment."""
        return now < self.open_until

    def trip(self, now: float) -> None:
        """Open the circuit for the next window."""
        self.open_until = now + CIRCUIT_OPEN_SECONDS


class EventEmitter:
    """XADD of a record into the stream, with the circuit in front.

    The client is created on the first write, so building the emitter
    (and the settings) never opens a connection.

    Three bounds guard the write and none of them is redundant: the
    connect and socket timeouts belong to the client and cover one
    socket operation each, while EMIT_TIMEOUT bounds the whole call,
    including whatever redis-py does between them. The write sits on
    the request path, so the total is the one that matters there.
    """

    timeout: float = EMIT_TIMEOUT

    def __init__(
        self,
        *,
        url: str,
        key: str,
        maxlen: int,
        enabled: bool,
    ) -> None:
        """Initialize the emitter.

        Args:
            url: Redis URL of the events buffer (LOGS_REDIS_URL).
            key: Name of the stream (LOGS_STREAM_KEY).
            maxlen: Approximate cap of the stream (LOGS_STREAM_MAXLEN).
            enabled: False makes every write a no-op (LOGS_BACKEND=none).

        """
        self._url = url
        self._key = key
        self._maxlen = maxlen
        self._enabled = enabled
        self._client: redis.Redis | None = None
        self.circuit = StreamCircuit()

    @property
    def client(self) -> redis.Redis:
        """Lazily built Redis client."""
        if self._client is None:
            self._client = redis.from_url(  # type: ignore[no-untyped-call]
                self._url,
                decode_responses=True,
                socket_connect_timeout=CONNECT_TIMEOUT,
                socket_timeout=SOCKET_TIMEOUT,
            )
        return self._client

    async def emit(self, event: Event) -> None:
        """Write the record; a failure is logged, never raised."""
        if not self._enabled:
            return
        now = _now()
        if self.circuit.is_open(now):
            self.circuit.dropped += 1
            return
        try:
            await asyncio.wait_for(self._xadd(event), timeout=self.timeout)
        except (redis.RedisError, OSError) as exc:
            self.circuit.trip(now)
            logger.warning(
                'Events stream is unavailable, events are dropped: %s',
                type(exc).__name__,
            )
            return
        if self.circuit.dropped:
            logger.warning(
                'Events stream is back, events dropped meanwhile: %s',
                self.circuit.dropped,
            )
            self.circuit.dropped = 0

    async def _xadd(self, event: Event) -> None:
        await self.client.xadd(
            name=self._key,
            fields={
                'type': event.type.value,
                'data': json.dumps(event.to_dict()),
            },
            maxlen=self._maxlen,
            approximate=True,
        )

    async def close(self) -> None:
        """Close the connection pool, if one was ever opened."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None


@lru_cache
def get_event_emitter() -> EventEmitter:
    """One emitter per process, the pattern of get_redis_client."""
    settings = get_settings()
    return EventEmitter(
        url=settings.LOGS_REDIS_URL,
        key=STREAM_KEY,
        maxlen=settings.LOGS_STREAM_MAXLEN,
        enabled=settings.logs_enabled,
    )


async def close_event_emitter() -> None:
    """Close the emitter and clear the cache for shutdown."""
    try:
        await get_event_emitter().close()
    finally:
        get_event_emitter.cache_clear()
