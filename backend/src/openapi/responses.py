from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    PolymorphicProxySerializer,
)
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
    reason = serializers.CharField(required=False)


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
FIELD_VALIDATION_ERROR = OpenApiResponse(
    response={
        'type': 'object',
        'additionalProperties': {
            'type': 'array',
            'items': {'type': 'string'},
        },
    },
    description='DRF field validation errors keyed by field name.',
    examples=[OpenApiExample(
        'Invalid API key name',
        value={'name': ['Ensure this field has no more than 200 characters.']},
        response_only=True,
    )],
)
FILTER_VALIDATION_ERROR = OpenApiResponse(
    response={
        'oneOf': [
            {'type': 'array', 'items': {'type': 'string'}},
            {
                'type': 'object',
                'additionalProperties': {
                    'type': 'array', 'items': {'type': 'string'},
                },
            },
        ],
    },
    description='Filter errors: a list of messages or field-keyed messages.',
    examples=[OpenApiExample(
        'Invalid filter', value=['Invalid filter value.'], response_only=True,
    )],
)

_ENRICHED_FIELD_ERROR = {
    'type': 'object',
    'properties': {
        name: {'type': 'string'}
        for name in ('message__', 'name__', 'api_name__', 'enriched__')
    },
    'required': ['message__', 'name__', 'api_name__', 'enriched__'],
}
_BULK_FIELD_ERRORS = {
    'type': 'object',
    'additionalProperties': {
        'type': 'array',
        'items': {'oneOf': [{'type': 'string'}, _ENRICHED_FIELD_ERROR]},
    },
}
BULK_VALIDATION_ERROR = OpenApiResponse(
    response={
        'oneOf': [
            {
                'type': 'object', 'required': ['code', 'message'],
                'properties': {
                    'code': {'type': 'string'},
                    'message': {'type': 'string'},
                    'details': {'type': 'object'},
                },
            },
            _BULK_FIELD_ERRORS,
            {'type': 'array', 'items': _BULK_FIELD_ERRORS},
        ],
    },
    description=(
        'Bulk item errors keep their list indexes and field names. Field '
        'messages may contain the original enriched validation metadata. '
        'Service errors use the usual code/message object.'
    ),
)
SSO_VALIDATION_ERROR = OpenApiResponse(
    response=PolymorphicProxySerializer(
        component_name='SSOValidationError',
        serializers=[
            ValidationErrorSerializer,
            serializers.ListSerializer(child=serializers.CharField()),
        ],
        resource_type_field_name=None,
        many=False,
    ),
    description=(
        'Field/business validation errors use code, message and details. '
        'An SSO-only account restriction returns an array of messages.'
    ),
    examples=[
        OpenApiExample(
            'SSO account restriction',
            value=[
                'This account uses SSO authentication. Please sign in '
                "through your organization's SSO portal.",
            ],
            response_only=True,
        ),
        VALIDATION_ERROR_EXAMPLE,
    ],
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
