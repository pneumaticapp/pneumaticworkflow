"""Security headers middleware.

Adds OWASP-recommended security headers to every response:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Content-Security-Policy: default-src 'none'
- Strict-Transport-Security (HSTS)
- X-XSS-Protection (legacy, but still recommended)
- Referrer-Policy
- Permissions-Policy
"""

from collections.abc import Callable

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response

# Headers applied to every response
_SECURITY_HEADERS: dict[str, str] = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Content-Security-Policy': "default-src 'none'",
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
}

# HSTS applied only in production (non-debug)
_HSTS_HEADER = (
    'Strict-Transport-Security',
    'max-age=31536000; includeSubDomains',
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    def __init__(
        self,
        app: Callable,
        *,
        include_hsts: bool = False,
    ) -> None:
        """Initialize security headers middleware.

        Args:
            app: ASGI application.
            include_hsts: If True, add HSTS header (production only).

        """
        super().__init__(app)
        self._include_hsts = include_hsts

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers[header] = value
        if self._include_hsts:
            response.headers[_HSTS_HEADER[0]] = _HSTS_HEADER[1]
        return response
