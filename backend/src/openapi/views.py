"""OpenAPI docs views with login redirect for browsers."""

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from drf_spectacular.views import (
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
)

LOGIN_PATH = '/auth/signin/'


class _LoginRedirectMixin:
    """Return 302 to frontend login instead of JSON 403.

    Used only on HTML docs pages (Swagger/ReDoc). Schema JSON
    at /api/schema/ must keep JSON 403 — a 302 HTML redirect
    breaks Swagger UI XHR schema fetch.
    """

    def handle_exception(self, exc: Exception) -> HttpResponse:
        if isinstance(
            exc, (NotAuthenticated, AuthenticationFailed),
        ):
            return redirect(f'{settings.FRONTEND_URL}{LOGIN_PATH}')
        return super().handle_exception(exc)


class DocsSwaggerView(_LoginRedirectMixin, SpectacularSwaggerView):
    pass


class DocsRedocView(_LoginRedirectMixin, SpectacularRedocView):
    pass
