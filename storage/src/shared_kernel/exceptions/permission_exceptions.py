"""Permission exceptions"""

from typing import Any, Optional

from .base_exceptions import BaseAppException
from .error_codes import PERMISSION_ERROR_CODES


class PermissionDeniedError(BaseAppException):
    """Permission denied error"""

    def __init__(
        self,
        details: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        error_code = PERMISSION_ERROR_CODES['PERMISSION_DENIED']
        super().__init__(error_code, details, **kwargs)


class AccessDeniedForPublicTokenError(BaseAppException):
    """Access denied for public token error"""

    def __init__(
        self,
        details: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        error_code = PERMISSION_ERROR_CODES['ACCESS_DENIED_PUBLIC_TOKEN']
        super().__init__(error_code, details, **kwargs)
