from django.http import HttpResponse, JsonResponse
from rest_framework.exceptions import APIException


def get_api_exception_response(ex: APIException) -> JsonResponse:
    detail = ex.detail
    if not isinstance(detail, dict):
        detail = {'detail': str(detail)}
    return JsonResponse(detail, status=ex.status_code)


def set_private_headers(response: HttpResponse) -> HttpResponse:
    """Prevent caching and referrer disclosure for sensitive responses."""
    response['Cache-Control'] = 'no-store'
    response['Referrer-Policy'] = 'no-referrer'
    return response
