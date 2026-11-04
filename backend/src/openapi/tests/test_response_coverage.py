"""Ensure every response declares a body or an explicit empty outcome."""

import pytest
from drf_spectacular.generators import SchemaGenerator

pytestmark = pytest.mark.django_db

_METHODS_REQUIRING_BODY = frozenset({
    'get', 'post', 'put', 'patch',
})

_DOCS_PREFIXES = (
    '/api/schema',
    '/api/docs',
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


def _has_response_body(responses: dict) -> bool:
    """Require a body unless success is explicitly empty or a redirect."""
    for status, response in responses.items():
        if status == '204' or status.startswith('3'):
            return True
        if not status.startswith('2'):
            continue
        if not isinstance(response, dict):
            continue
        if response.get('content'):
            return True
    return False


def test_public_endpoints__response_body__ok():
    """Fail when a public GET/POST/PUT/PATCH endpoint
    has no response body documented.

    Empty successes use 204 and redirects use their 3xx status;
    no operation-name whitelist can hide an incomplete response.
    """

    # arrange
    generator = SchemaGenerator()
    schema = generator.get_schema(
        request=None, public=True,
    )
    paths = schema.get('paths') or {}

    # act
    missing = []
    for path, operations in paths.items():
        if _is_docs_path(path):
            continue
        for method, operation in operations.items():
            if method not in _METHODS_REQUIRING_BODY:
                continue
            if not isinstance(operation, dict):
                continue
            op_id = operation.get('operationId', '')
            responses = operation.get('responses') or {}
            if not _has_response_body(responses):
                missing.append(
                    f'{method.upper()} {path} ({op_id})',
                )

    # assert
    assert missing == [], (
        'Endpoints without response body documented:\n'
        + '\n'.join(f'  - {m}' for m in missing)
    )
