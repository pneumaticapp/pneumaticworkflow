import json
from typing import Optional
from urllib.parse import quote

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.urls import reverse

OAUTH_ERROR_STATUS = 400


def get_oauth_error_response(
    error: str,
    status: int = OAUTH_ERROR_STATUS,
    description: Optional[str] = None,
) -> JsonResponse:
    """RFC 6749 error body: `{"error": ..., "error_description": ...}`."""
    body = {'error': error}
    if description is not None:
        body['error_description'] = description
    return JsonResponse(body, status=status)


def get_public_registration_response(response: HttpResponse) -> HttpResponse:
    """Point the management URI at the public issuer, not the backend."""
    if response.status_code not in {200, 201}:
        return response
    data = json.loads(response.content)
    if 'registration_client_uri' in data:
        data['registration_client_uri'] = (
            settings.MCP_ISSUER_URL
            + reverse('oauth2_provider:dcr-register')
            + '/'
            + quote(data['client_id'], safe='')
        )
        response.content = json.dumps(data)
    return response
