from urllib.parse import urlparse

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class FileServiceAuthMiddleware(MiddlewareMixin):
    """
    Middleware for setting authorization cookie for file service.
    Sets cookie with authorization token for file access.
    """

    def process_response(self, request, response):
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

        # Get domain from FRONTEND_URL
        domain = self._get_cookie_domain()

        # Set cookie for file service authorization
        response.set_cookie(
            key='file_service_auth',
            value=auth_token,
            domain=domain,
            secure=not settings.DEBUG,
            httponly=True,
            samesite='Lax',
        )

        return response

    def _get_auth_token(self, request):
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
        if hasattr(request, 'COOKIES'):
            jwt_token = request.COOKIES.get('access_token')
            if jwt_token:
                return jwt_token

        return None

    def _get_cookie_domain(self):
        """
        Gets cookie domain from settings.
        Extracts domain from FRONTEND_URL.
        """
        frontend_url = settings.FRONTEND_URL

        if not frontend_url:
            return None

        # Extract domain from URL
        try:
            parsed = urlparse(frontend_url)
            return parsed.hostname
        except (ValueError, AttributeError):
            return None
