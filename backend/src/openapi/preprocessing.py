"""Add legacy methods and filter the public OpenAPI schema."""

from functools import wraps
from typing import Any, List, Sequence, Tuple

from src.openapi.enums import EXCLUDED_OPERATIONS

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


def exclude_private_endpoints(
    endpoints: Sequence[Endpoint],
) -> List[Endpoint]:
    """Exclude specific HTTP operations from the public schema."""
    return [
        (path, regex, method, callback)
        for path, regex, method, callback in endpoints
        if (method, path.replace('{pk}', '{id}')) not in EXCLUDED_OPERATIONS
    ]
