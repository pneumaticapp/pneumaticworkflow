from typing import Type

from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from rest_framework import serializers

from src.openapi.entities import PermissionDoc

LIMIT_OFFSET_LEGACY_NOTE = (
    'With limit/offset — paginated envelope. '
    'Without limit/offset — flat array (legacy).'
)


def error_response(
    serializer: Type[serializers.Serializer],
    description: str,
    example: OpenApiExample,
) -> OpenApiResponse:
    return OpenApiResponse(
        response=serializer,
        description=description,
        examples=[example],
    )


def paginated_serializer(
    item_serializer: Type[serializers.Serializer],
    name: str,
) -> Type[serializers.Serializer]:
    """LimitOffset pagination envelope matching project API."""

    class PaginatedSerializer(serializers.Serializer):
        count = serializers.IntegerField()
        next = serializers.CharField(
            allow_null=True,
            required=False,
        )
        previous = serializers.CharField(
            allow_null=True,
            required=False,
        )
        results = item_serializer(many=True)

    PaginatedSerializer.__name__ = name
    return PaginatedSerializer


def access_description(
    *permission_keys: str,
    intro: str = 'Who can call this endpoint:',
) -> str:
    """Build markdown Access block for OpenAPI description."""
    lines = ['## Access', intro]
    for key in permission_keys:
        lines.append(f'- {getattr(PermissionDoc, key)}')
    return '\n'.join(lines)


def with_access_text(description: str, access: str) -> str:
    """Prepend free-text to a ready Access block (ACCESS_*)."""
    text = description.strip()
    if not text:
        return access
    return f'{text}\n\n{access}'
