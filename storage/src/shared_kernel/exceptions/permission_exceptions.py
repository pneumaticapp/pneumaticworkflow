"""Permission exceptions"""

from .base_exceptions import BaseAppError
from .error_codes import PERMISSION_ERROR_CODES


class PermissionDeniedError(BaseAppError):
    """Permission denied error"""

    def __init__(
        self,
        details: str | None = None,
        **kwargs: str | int | None,
    ) -> None:
        error_code = PERMISSION_ERROR_CODES['PERMISSION_DENIED']
        super().__init__(error_code, details, **kwargs)


class AccessDeniedForPublicTokenError(BaseAppError):
    """Access denied for public token error"""

    def __init__(
        self,
        details: str | None = None,
        **kwargs: str | int | None,
    ) -> None:
        error_code = PERMISSION_ERROR_CODES['ACCESS_DENIED_PUBLIC_TOKEN']
        super().__init__(error_code, details, **kwargs)
