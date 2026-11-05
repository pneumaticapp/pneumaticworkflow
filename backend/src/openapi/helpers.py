from typing import Callable, Type, TypeVar

from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from rest_framework import serializers

from src.openapi.entities import PermissionDoc

ViewMethod = TypeVar('ViewMethod', bound=Callable)


def unpaginated_schema(method: ViewMethod) -> ViewMethod:
    """Disable inferred pagination without changing runtime view settings.

    Apply above @extend_schema on actions returning a plain list.
    """
    base_schema = method.kwargs['schema']

    class UnpaginatedSchema(base_schema):
        def _get_paginator(self):
            return None

    method.kwargs['schema'] = UnpaginatedSchema
    return method


def single_response_schema(method: ViewMethod) -> ViewMethod:
    """Describe one object on views whose names imply a collection."""
    base_schema = method.kwargs['schema']

    class SingleResponseSchema(base_schema):
        def _is_list_view(self, serializer=None) -> bool:
            return False

        def _get_paginator(self):
            return None

    method.kwargs['schema'] = SingleResponseSchema
    return method


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
