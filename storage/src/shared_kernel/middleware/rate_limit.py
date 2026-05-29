"""In-memory rate limiter middleware.

Uses a sliding window counter per client IP.
Zero external dependencies — no slowapi needed.
"""

import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


@dataclass
class _RateLimit:
    """Rate limit configuration for a route."""

    max_requests: int
    window_seconds: int


@dataclass
class _SlidingWindow:
    """Sliding window counter for a client."""

    timestamps: list[float] = field(default_factory=list)

    def count_in_window(self, now: float, window: int) -> int:
        """Count requests within the time window."""
        cutoff = now - window
        self.timestamps = [
            ts for ts in self.timestamps if ts > cutoff
        ]
        return len(self.timestamps)

    def record(self, now: float) -> None:
        """Record a new request."""
        self.timestamps.append(now)


# Route patterns → limits
_RATE_LIMITS: dict[str, _RateLimit] = {
    'upload': _RateLimit(max_requests=10, window_seconds=60),
    'download': _RateLimit(max_requests=100, window_seconds=60),
}


def _classify_route(path: str, method: str) -> str | None:
    """Classify request into rate limit bucket.

    Returns bucket name or None if not rate-limited.
    """
    if method == 'POST' and path == '/upload':
        return 'upload'
    if method == 'GET' and path not in {
        '/', '/upload', '/docs', '/redoc',
        '/openapi.json', '/health',
    } and len(path) > 1:
        # GET /{file_id} pattern
        return 'download'
    return None


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For."""
    forwarded = request.headers.get('x-forwarded-for')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.client.host if request.client else '0.0.0.0'


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window."""

    def __init__(
        self,
        app: Callable,
        rate_limits: dict[str, _RateLimit] | None = None,
        *,
        enabled: bool = True,
    ) -> None:
        """Initialize rate limiter.

        Args:
            app: ASGI application.
            rate_limits: Custom rate limits (default: module-level).
            enabled: If False, skip rate limiting (for tests).

        """
        super().__init__(app)
        self._limits = rate_limits or _RATE_LIMITS
        self._enabled = enabled
        # {bucket:ip -> SlidingWindow}
        self._windows: dict[
            str, _SlidingWindow,
        ] = defaultdict(_SlidingWindow)

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Check rate limit before processing request."""
        if not self._enabled:
            return await call_next(request)
        bucket = _classify_route(
            request.url.path,
            request.method,
        )
        if bucket is None or bucket not in self._limits:
            return await call_next(request)

        limit = self._limits[bucket]
        client_ip = _get_client_ip(request)
        key = f'{bucket}:{client_ip}'
        now = time.monotonic()

        window = self._windows[key]
        current = window.count_in_window(
            now, limit.window_seconds,
        )

        if current >= limit.max_requests:
            retry_after = limit.window_seconds
            return JSONResponse(
                status_code=429,
                content={
                    'detail': 'Rate limit exceeded',
                    'retry_after': retry_after,
                },
                headers={
                    'Retry-After': str(retry_after),
                },
            )

        window.record(now)
        return await call_next(request)
