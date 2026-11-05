"""Schema-only endpoint additions and an optional public-only filter."""

from functools import wraps
from typing import Any, Iterable, List, Optional, Sequence, Tuple

from src.authentication.permissions import PrivateApiPermission
from src.generics.permissions import StagingPermission
from src.openapi.enums import ExcludedPath

Endpoint = Tuple[str, str, str, Any]

_LEGACY_HTTP_METHODS = {
    ('/accounts/user', 'src.accounts.views.user.UserViewSet'): 'put',
    ('/tenants/{pk}', 'src.accounts.views.tenants.TenantsViewSet'): 'patch',
}


def _schema_callback(callback: Any, method: str) -> Any:
    @wraps(callback)
    def replacement(*args: Any, **kwargs: Any) -> Any:
        return callback(*args, **kwargs)

    replacement.actions = {**callback.actions, method: method}
    return replacement


def include_legacy_http_methods(
    endpoints: Sequence[Endpoint],
) -> List[Endpoint]:
    """Expose legacy handlers that DRF dispatches outside router actions.

    Only schema callbacks receive the extra action mapping. The callbacks
    registered in urlpatterns and their runtime action maps stay untouched.
    """
    result = list(endpoints)
    registered = {(path, method) for path, _, method, _ in endpoints}
    for path, regex, _method, callback in endpoints:
        view = callback.cls
        method = _LEGACY_HTTP_METHODS.get((
            path, f'{view.__module__}.{view.__name__}',
        ))
        if not method or (path, method.upper()) in registered:
            continue
        result.append((
            path, regex, method.upper(), _schema_callback(callback, method),
        ))
        registered.add((path, method.upper()))
    return result


_EXCLUDED_PERMISSIONS = (
    PrivateApiPermission,
    StagingPermission,
)


def exclude_private_endpoints(
    endpoints: Sequence[Endpoint],
) -> List[Endpoint]:
    """Drop private, staging and internal ops from the OpenAPI schema."""
    filtered: List[Endpoint] = []
    for path, path_regex, method, callback in endpoints:
        if _should_exclude(path, method, callback):
            continue
        filtered.append((path, path_regex, method, callback))
    return filtered


def _should_exclude(
    path: str,
    method: str,
    callback: Any,
) -> bool:
    normalized = path.rstrip('/') or '/'
    for prefix in ExcludedPath.ALL:
        if normalized == prefix or normalized.startswith(
            f'{prefix}/',
        ):
            return True
    return _has_excluded_permission(callback, method)


def _has_excluded_permission(
    callback: Any,
    method: str,
) -> bool:
    for perm in _iter_permission_classes(callback, method):
        perm_cls = perm if isinstance(perm, type) else type(perm)
        if perm_cls in _EXCLUDED_PERMISSIONS:
            return True
        if issubclass(perm_cls, _EXCLUDED_PERMISSIONS):
            return True
    return False


def _iter_permission_classes(
    callback: Any,
    method: str,
) -> Iterable[Any]:
    view_cls: Optional[type] = getattr(callback, 'cls', None)
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
                # Some get_permissions() read self.request; it is
                # absent during schema generation.
                pass

    return getattr(view_cls, 'permission_classes', ()) or ()
