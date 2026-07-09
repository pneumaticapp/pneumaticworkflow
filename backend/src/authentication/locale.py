from django.utils import translation
from rest_framework.request import Request


def resolve_request_language(request: Request) -> str:
    """Return locale after DRF authentication."""
    user = getattr(request, 'user', None)
    if user and not user.is_anonymous and hasattr(user, 'language'):
        return user.language
    return translation.get_language_from_request(request)


def install_api_locale_activation():
    """Hook APIView.perform_authentication to set per-request locale."""
    from rest_framework.views import APIView

    if getattr(APIView.perform_authentication, '_locale_hook_installed', False):
        return

    original = APIView.perform_authentication

    def perform_authentication_with_locale(self, request: Request):
        original(self, request)
        translation.activate(resolve_request_language(request))

    perform_authentication_with_locale._locale_hook_installed = True
    APIView.perform_authentication = perform_authentication_with_locale
