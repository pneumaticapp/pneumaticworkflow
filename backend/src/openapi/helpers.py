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


def access_description(
    *permission_keys: str,
    intro: str = 'Who can call this endpoint:',
) -> str:
    """Build markdown Access block for OpenAPI description."""
    lines = ['## Access', intro]
    for key in permission_keys:
        text = getattr(PermissionDoc, key, None)
        if text is None:
            raise ValueError(f'Unknown permission key: {key}')
        lines.append(f'- {text}')
    return '\n'.join(lines)


def with_access_text(description: str, access: str) -> str:
    """Prepend free-text to a ready Access block (ACCESS_*)."""
    text = description.strip()
    if not text:
        return access
    return f'{text}\n\n{access}'
