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

from src.shared_kernel.config import get_settings


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
        self.timestamps = [ts for ts in self.timestamps if ts > cutoff]
        return len(self.timestamps)

    def record(self, now: float) -> None:
        """Record a new request."""
        self.timestamps.append(now)


def _get_default_limits() -> dict[str, _RateLimit]:
    """Get default rate limits from settings."""
    settings = get_settings()
    return {
        'upload': _RateLimit(
            max_requests=settings.RATE_LIMIT_UPLOAD_REQUESTS,
            window_seconds=settings.RATE_LIMIT_UPLOAD_WINDOW,
        ),
        'download': _RateLimit(
            max_requests=settings.RATE_LIMIT_DOWNLOAD_REQUESTS,
            window_seconds=settings.RATE_LIMIT_DOWNLOAD_WINDOW,
        ),
    }


def _classify_route(path: str, method: str) -> str | None:
    """Classify request into rate limit bucket.

    Returns bucket name or None if not rate-limited.
    """
    if method == 'POST' and path == '/upload':
        return 'upload'
    if (
        method == 'GET'
        and path
        not in {
            '/',
            '/upload',
            '/docs',
            '/redoc',
            '/openapi.json',
            '/health',
        }
        and len(path) > 1
    ):
        # GET /{file_id} pattern
        return 'download'
    return None


def _get_client_ip(request: Request) -> str:
    """Extract client IP securely.

    Relies on X-Real-IP set by Nginx ($remote_addr).
    Ignores X-Forwarded-For which can be spoofed by clients.
    """
    real_ip = request.headers.get('x-real-ip')
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else '0.0.0.0'  # noqa: S104


_CLEANUP_INTERVAL_SECONDS = 60


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
        self._limits = rate_limits or _get_default_limits()
        self._enabled = enabled
        # {bucket:ip -> SlidingWindow}
        self._windows: dict[
            str,
            _SlidingWindow,
        ] = defaultdict(_SlidingWindow)
        self._max_window_seconds = max(
            (lim.window_seconds for lim in self._limits.values()),
            default=60,
        )
        self._last_cleanup = time.monotonic()

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

        self._maybe_evict_stale(now)

        window = self._windows[key]
        current = window.count_in_window(
            now,
            limit.window_seconds,
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

    def _maybe_evict_stale(self, now: float) -> None:
        """Remove windows with no recent activity.

        Runs at most once per _CLEANUP_INTERVAL_SECONDS to avoid
        scanning the dict on every request.
        """
        if now - self._last_cleanup < _CLEANUP_INTERVAL_SECONDS:
            return
        self._last_cleanup = now
        cutoff = now - self._max_window_seconds
        stale_keys = [
            key
            for key, win in self._windows.items()
            if not win.timestamps or win.timestamps[-1] <= cutoff
        ]
        for key in stale_keys:
            del self._windows[key]
