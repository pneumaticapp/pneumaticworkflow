"""Ensure every public endpoint has @extend_schema."""

import pytest
from drf_spectacular.generators import EndpointEnumerator
from drf_spectacular.openapi import AutoSchema

pytestmark = pytest.mark.django_db

_DOCS_PREFIXES = (
    '/api/schema',
    '/api/docs',
    '/api/redoc',
)

_THIRD_PARTY_VIEWS = (
    'TokenRefreshView',
)


def _is_docs_path(path: str) -> bool:
    normalized = path.rstrip('/')
    for prefix in _DOCS_PREFIXES:
        if (
            normalized == prefix
            or normalized.startswith(f'{prefix}/')
        ):
            return True
    return False


def _has_class_level_schema(view_cls) -> bool:
    """Class decorated with @extend_schema or @extend_schema(exclude)."""
    schema = view_cls.__dict__.get('schema')
    if schema is None:
        return False
    schema_cls = schema if isinstance(schema, type) else type(schema)
    return schema_cls is not AutoSchema


_GENERIC_METHOD_MAP = {
    'get': ('list', 'retrieve'),
    'post': ('create',),
    'put': ('update',),
    'patch': ('partial_update',),
    'delete': ('destroy',),
}


def _has_method_level_schema(
    view_cls,
    method: str,
    callback,
) -> bool:
    actions = getattr(callback, 'actions', None)
    if actions:
        candidates = [actions.get(method.lower())]
    else:
        candidates = [
            method.lower(),
            *_GENERIC_METHOD_MAP.get(method.lower(), ()),
        ]
    for name in candidates:
        if not name:
            continue
        view_method = getattr(view_cls, name, None)
        if view_method is None:
            continue
        if 'schema' in getattr(view_method, 'kwargs', {}):
            return True
    return False


def _has_extend_schema(callback, method: str) -> bool:
    view_cls = getattr(callback, 'cls', None)
    if view_cls is None:
        return False
    if view_cls.__name__ in _THIRD_PARTY_VIEWS:
        return True
    if _has_class_level_schema(view_cls):
        return True
    return _has_method_level_schema(
        view_cls, method, callback,
    )


def test_public_endpoints__all_decorated__ok():
    """Fail when a public endpoint lacks @extend_schema.

    EndpointEnumerator already applies preprocessing hooks
    (exclude_private_endpoints), so we only check what
    remains — the public surface.
    """

    # arrange
    enumerator = EndpointEnumerator()
    endpoints = enumerator.get_api_endpoints()

    # act
    missing = []
    for path, _regex, method, callback in endpoints:
        if _is_docs_path(path):
            continue
        if not _has_extend_schema(callback, method):
            view_cls = getattr(callback, 'cls', None)
            cls_name = (
                view_cls.__name__ if view_cls else '?'
            )
            actions = getattr(
                callback, 'actions', None,
            )
            action = ''
            if actions:
                action = actions.get(
                    method.lower(), '',
                )
            label = (
                f'{method} {path}'
                f' ({cls_name}.{action})'
            )
            missing.append(label)

    # assert
    assert missing == [], (
        'Public endpoints without @extend_schema:\n'
        + '\n'.join(f'  - {m}' for m in missing)
    )
