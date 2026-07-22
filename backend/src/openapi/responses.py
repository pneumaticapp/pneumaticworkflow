from drf_spectacular.utils import OpenApiResponse
from rest_framework import serializers

from src.openapi.examples import (
    FORBIDDEN_EXAMPLE,
    NOT_FOUND_EXAMPLE,
    TOO_MANY_REQUESTS_EXAMPLE,
    UNAUTHORIZED_EXAMPLE,
    VALIDATION_ERROR_EXAMPLE,
)
from src.openapi.helpers import error_response

# Empty body (200 OK / 204 No Content without response schema)
EMPTY = OpenApiResponse(description='Success')


class ValidationErrorDetailsSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    api_name = serializers.CharField(required=False)
    task = serializers.CharField(required=False)
    field = serializers.CharField(required=False)
    reason = serializers.CharField()


class ValidationErrorSerializer(serializers.Serializer):
    """Agreed validation error body (code=validation_error)."""

    message = serializers.CharField()
    code = serializers.CharField()
    details = ValidationErrorDetailsSerializer(required=False)


class DetailErrorSerializer(serializers.Serializer):
    """DRF default error body for 401/403/404/429."""

    detail = serializers.CharField()


# Shared error responses for extend_schema(responses={...})
VALIDATION_ERROR = error_response(
    serializer=ValidationErrorSerializer,
    description='Validation error',
    example=VALIDATION_ERROR_EXAMPLE,
)
UNAUTHORIZED = error_response(
    serializer=DetailErrorSerializer,
    description='Not authenticated',
    example=UNAUTHORIZED_EXAMPLE,
)
FORBIDDEN = error_response(
    serializer=DetailErrorSerializer,
    description='Permission denied',
    example=FORBIDDEN_EXAMPLE,
)
NOT_FOUND = error_response(
    serializer=DetailErrorSerializer,
    description='Not found',
    example=NOT_FOUND_EXAMPLE,
)
TOO_MANY_REQUESTS = error_response(
    serializer=DetailErrorSerializer,
    description='Rate limit exceeded',
    example=TOO_MANY_REQUESTS_EXAMPLE,
)
