"""Verify documented Access blocks match actual permissions."""

import re
from typing import Any, Dict, Iterable, Optional, Set, Tuple

import pytest
from drf_spectacular.generators import (
    EndpointEnumerator,
    SchemaGenerator,
)

from src.openapi.entities import PermissionDoc

pytestmark = pytest.mark.django_db

Endpoint = Tuple[str, str, str, Any]

# Pre-existing doc/code mismatches to fix separately.
# Format: (operationId,)
_KNOWN_MISMATCHES = frozenset({
    # Docs claim UserIsAuthenticated + gates,
    # but code uses broader IsAuthenticated.
    'accounts_account_retrieve',
    'accounts_account_update',
    'accounts_user_activate_vacation_create',
    'accounts_user_contacts_retrieve',
    'accounts_user_counters_retrieve',
    'accounts_user_deactivate_vacation_create',
    # Docs say BillingPlanPermission, code omits it
    # for list action.
    'accounts_user_list',
    # Docs use ACCESS_HIGHLIGHTS instead of
    # ACCESS_DASHBOARD (copy-paste error).
    'reports_dashboard_workflows_breakdown_list',
    'reports_dashboard_workflows_by_tasks_list',
    'reports_dashboard_workflows_overview_retrieve',
})

_DOCS_PREFIXES = (
    '/api/schema',
    '/api/docs',
    '/api/swagger',
)

_ACCESS_LINE_RE = re.compile(r'^-\s+(.+)$')


def _build_text_to_key_map() -> Dict[str, str]:
    mapping = {}
    for key in dir(PermissionDoc):
        if key.startswith('_'):
            continue
        text = getattr(PermissionDoc, key)
        if isinstance(text, str):
            mapping[text] = key
    return mapping


_TEXT_TO_KEY = _build_text_to_key_map()


def _is_docs_path(path: str) -> bool:
    normalized = path.rstrip('/')
    for prefix in _DOCS_PREFIXES:
        if (
            normalized == prefix
            or normalized.startswith(f'{prefix}/')
        ):
            return True
    return False


def _parse_access_keys(description: str) -> Optional[Set[str]]:
    """Extract permission keys from ## Access block.

    Returns None if description has no Access block.
    """
    lines = description.split('\n')
    in_access = False
    keys: Set[str] = set()
    for line in lines:
        stripped = line.strip()
        if stripped == '## Access':
            in_access = True
            continue
        if in_access and stripped.startswith('## '):
            break
        if not in_access:
            continue
        match = _ACCESS_LINE_RE.match(stripped)
        if match:
            text = match.group(1).strip()
            key = _TEXT_TO_KEY.get(text)
            if key is not None:
                keys.add(key)
    if not in_access:
        return None
    return keys


def _iter_permission_classes(
    callback: Any,
    method: str,
) -> Iterable[Any]:
    """Resolve permission instances for an endpoint.

    Mirrors preprocessing._iter_permission_classes.
    """
    view_cls: Optional[type] = getattr(
        callback, 'cls', None,
    )
    if view_cls is None:
        return ()

    actions = getattr(callback, 'actions', None)
    if (
        actions is not None
        and hasattr(view_cls, 'get_permissions')
    ):
        action_name = actions.get(method.lower())
        if action_name is not None:
            view = view_cls()
            view.action = action_name
            view.args = ()
            view.kwargs = {}
            try:
                return tuple(view.get_permissions())
            except AttributeError:
                pass

    return getattr(
        view_cls, 'permission_classes', (),
    ) or ()


def _actual_permission_keys(
    callback: Any,
    method: str,
) -> Set[str]:
    """Get PermissionDoc keys for actual permissions."""
    keys: Set[str] = set()
    for perm in _iter_permission_classes(callback, method):
        cls = perm if isinstance(perm, type) else type(perm)
        name = cls.__name__
        if hasattr(PermissionDoc, name):
            keys.add(name)
    return keys


def test_access_blocks__vs_get_perms__match():
    """Fail when an Access block disagrees with
    get_permissions().

    For each public endpoint whose @extend_schema
    description contains ## Access, parse the listed
    permissions and compare them to the permission
    set returned by the view at runtime.
    """

    # arrange
    generator = SchemaGenerator()
    schema = generator.get_schema(
        request=None, public=True,
    )
    paths = schema.get('paths') or {}

    enumerator = EndpointEnumerator()
    endpoints = enumerator.get_api_endpoints()
    ep_map: Dict[Tuple[str, str], Any] = {}
    for path, _regex, method, callback in endpoints:
        ep_map[(path, method.lower())] = callback

    # act
    mismatches = []
    for path, operations in paths.items():
        if _is_docs_path(path):
            continue
        for method, operation in operations.items():
            if not isinstance(operation, dict):
                continue
            description = operation.get(
                'description', '',
            )
            doc_keys = _parse_access_keys(description)
            if doc_keys is None:
                continue

            callback = ep_map.get((path, method))
            if callback is None:
                continue

            actual_keys = _actual_permission_keys(
                callback, method,
            )

            op_id = operation.get(
                'operationId', '',
            )
            if op_id in _KNOWN_MISMATCHES:
                continue

            if doc_keys != actual_keys:
                only_doc = doc_keys - actual_keys
                only_actual = actual_keys - doc_keys
                parts = [
                    f'{method.upper()} {path}'
                    f' ({op_id})',
                ]
                if only_doc:
                    parts.append(
                        f'  doc-only: {sorted(only_doc)}',
                    )
                if only_actual:
                    parts.append(
                        f'  code-only: '
                        f'{sorted(only_actual)}',
                    )
                mismatches.append('\n'.join(parts))

    # assert
    assert mismatches == [], (
        'Access block / get_permissions() mismatch:\n'
        + '\n'.join(f'  - {m}' for m in mismatches)
    )
