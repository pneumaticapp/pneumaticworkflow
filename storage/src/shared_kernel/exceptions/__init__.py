"""Centralized exception system."""

from .auth_exceptions import (
    AuthenticationError,
)
from .base_exceptions import (
    BaseAppError,
    ErrorCode,
    ErrorResponse,
    ErrorType,
)
from .database_exceptions import (
    DatabaseConnectionError,
    DatabaseConstraintError,
    DatabaseError,
    DatabaseOperationError,
)
from .domain_exceptions import (
    DomainFileNotFoundError,
    FileAccessDeniedError,
    FileSizeExceededError,
    StorageError,
)
from .error_codes import (
    AUTH_ERROR_CODES,
    DATABASE_ERROR_CODES,
    DOMAIN_ERROR_CODES,
    EXTERNAL_SERVICE_ERROR_CODES,
    INFRA_ERROR_CODES,
    PERMISSION_ERROR_CODES,
    VALIDATION_ERROR_CODES,
)
from .error_messages import (
    MSG_DB_009,
    MSG_DB_010,
    MSG_EXT_011,
    MSG_EXT_012,
    MSG_EXT_013,
    MSG_EXT_014,
    MSG_STORAGE_009,
    MSG_STORAGE_010,
    MSG_STORAGE_011,
)
from .exception_handler import (
    create_error_response,
    register_exception_handlers,
)
from .external_service_exceptions import (
    ExternalServiceError,
    HttpClientError,
    HttpTimeoutError,
    RedisConnectionError,
    RedisOperationError,
)
from .permission_exceptions import (
    PermissionDeniedError,
)

__all__ = [
    'AUTH_ERROR_CODES',
    'DATABASE_ERROR_CODES',
    'DOMAIN_ERROR_CODES',
    'EXTERNAL_SERVICE_ERROR_CODES',
    'INFRA_ERROR_CODES',
    'MSG_DB_009',
    'MSG_DB_010',
    'MSG_EXT_011',
    'MSG_EXT_012',
    'MSG_EXT_013',
    'MSG_EXT_014',
    'MSG_STORAGE_009',
    'MSG_STORAGE_010',
    'MSG_STORAGE_011',
    'PERMISSION_ERROR_CODES',
    'VALIDATION_ERROR_CODES',
    'AuthenticationError',
    'BaseAppError',
    'DatabaseConnectionError',
    'DatabaseConstraintError',
    'DatabaseError',
    'DatabaseOperationError',
    'DomainFileNotFoundError',
    'ErrorCode',
    'ErrorResponse',
    'ErrorType',
    'ExternalServiceError',
    'FileAccessDeniedError',
    'FileSizeExceededError',
    'HttpClientError',
    'HttpTimeoutError',
    'PermissionDeniedError',
    'RedisConnectionError',
    'RedisOperationError',
    'StorageError',
    'create_error_response',
    'register_exception_handlers',
]
