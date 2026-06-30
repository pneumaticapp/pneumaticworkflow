from typing import Optional
from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

COOKIE_NAME = 'file_service_auth'
COOKIE_MAX_AGE = 86400  # 24 hours


class FileServiceAuthMiddleware(MiddlewareMixin):
    """
    Middleware for setting authorization cookie for file service.
    Sets cookie with authorization token for file access.
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)
        self._cookie_domain = self._resolve_cookie_domain()

    def process_response(
        self, request: HttpRequest, response: HttpResponse,
    ) -> HttpResponse:
        """
        Sets authorization cookie for file service.
        """
        # Check if user is authenticated
        if not hasattr(request, 'user') or not request.user:
            return response

        if not request.user.is_authenticated:
            return response

        # Get authorization token
        auth_token = self._get_auth_token(request)
        if not auth_token:
            return response

        # Skip if cookie already matches (avoid redundant Set-Cookie headers)
        existing_token = request.COOKIES.get(COOKIE_NAME)
        if existing_token == auth_token:
            return response

        # Set cookie for file service authorization
        response.set_cookie(
            key=COOKIE_NAME,
            value=auth_token,
            domain=self._cookie_domain,
            path='/',
            max_age=COOKIE_MAX_AGE,
            secure=not settings.DEBUG,
            httponly=True,
            samesite='Lax',
        )

        return response

    def _get_auth_token(
        self, request: HttpRequest,
    ) -> Optional[str]:
        """
        Gets authorization token from request.
        Supports various token types.
        """
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if (
                auth_header.startswith('Bearer ') or
                auth_header.startswith('Token ')
        ):
            return auth_header.split(' ')[1]

        # Get token from cookie (for JWT)
        jwt_token = request.COOKIES.get('access_token')
        if jwt_token:
            return jwt_token

        return None

    @staticmethod
    def _resolve_cookie_domain() -> Optional[str]:
        """
        Extracts root domain from FRONTEND_URL for cross-subdomain
        cookie sharing.

        Returns root domain (e.g. '.pneumatic.app') so that a cookie
        set by api-dev.pneumatic.app is also visible on
        dev.pneumatic.app and dev.pneumatic.app/files/*.
        Without this, the browser rejects Set-Cookie because
        api-dev ≠ dev (RFC 6265 domain-match).
        """
        frontend_url = settings.FRONTEND_URL
        if not frontend_url:
            return None
        hostname = urlparse(frontend_url).hostname
        if not hostname or '.' not in hostname:
            return None
        return '.' + '.'.join(hostname.split('.')[-2:])
