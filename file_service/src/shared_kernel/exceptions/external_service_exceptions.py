"""External service exceptions"""

from typing import Any, Optional

from .base_exceptions import BaseAppException
from .error_codes import EXTERNAL_SERVICE_ERROR_CODES
from .error_messages import (
    MSG_EXT_004,
    MSG_EXT_006,
    MSG_EXT_008,
    MSG_EXT_010,
)


class ExternalServiceError(BaseAppException):
    """Base external service error"""

    def __init__(
        self,
        error_code_key: str,
        details: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        error_code = EXTERNAL_SERVICE_ERROR_CODES[error_code_key]
        super().__init__(error_code, details, **kwargs)


class RedisConnectionError(ExternalServiceError):
    """Redis connection error"""

    def __init__(
        self,
        details: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__('REDIS_CONNECTION_ERROR', details, **kwargs)


class RedisOperationError(ExternalServiceError):
    """Redis operation error"""

    def __init__(
        self,
        operation: str,
        details: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        custom_details = MSG_EXT_004.format(operation=operation)
        if details:
            custom_details += f': {details}'
        super().__init__('REDIS_OPERATION_ERROR', custom_details, **kwargs)


class HttpClientError(ExternalServiceError):
    """HTTP client error"""

    def __init__(
        self,
        url: str,
        status_code: Optional[int] = None,
        details: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        custom_details = MSG_EXT_006.format(url=url)
        if status_code:
            custom_details += f' with status {status_code}'
        if details:
            custom_details += f': {details}'
        super().__init__('HTTP_CLIENT_ERROR', custom_details, **kwargs)


class HttpTimeoutError(ExternalServiceError):
    """HTTP timeout error"""

    def __init__(
        self,
        url: str,
        timeout: float,
        details: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        custom_details = MSG_EXT_008.format(url=url, timeout=timeout)
        if details:
            custom_details += f': {details}'
        super().__init__('HTTP_TIMEOUT_ERROR', custom_details, **kwargs)


class ExternalServiceUnavailableError(ExternalServiceError):
    """External service unavailable error"""

    def __init__(
        self,
        service_name: str,
        details: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        custom_details = MSG_EXT_010.format(service_name=service_name)
        if details:
            custom_details += f': {details}'
        super().__init__(
            'EXTERNAL_SERVICE_UNAVAILABLE', custom_details, **kwargs
        )
