"""Error codes catalog."""

from .base_exceptions import ErrorCode, ErrorType
from .error_messages import (
    MSG_AUTH_001,
    MSG_DB_001,
    MSG_DB_003,
    MSG_DB_007,
    MSG_EXT_001,
    MSG_EXT_003,
    MSG_EXT_005,
    MSG_EXT_007,
    MSG_FILE_001,
    MSG_FILE_004,
    MSG_FILE_006,
    MSG_PERM_001,
    MSG_STORAGE_001,
    MSG_STORAGE_003,
    MSG_STORAGE_005,
    MSG_STORAGE_007,
    MSG_VAL_001,
)

# Domain error codes
DOMAIN_ERROR_CODES = {
    'FILE_NOT_FOUND': ErrorCode(
        code='FILE_001',
        message=MSG_FILE_001,
        error_type=ErrorType.DOMAIN,
        http_status=404,
    ),
    'FILE_ACCESS_DENIED': ErrorCode(
        code='FILE_002',
        message=MSG_FILE_004,
        error_type=ErrorType.AUTHORIZATION,
        http_status=403,
    ),
    'FILE_SIZE_EXCEEDED': ErrorCode(
        code='FILE_003',
        message=MSG_FILE_006,
        error_type=ErrorType.VALIDATION,
        http_status=413,
    ),
    'STORAGE_OPERATION_FAILED': ErrorCode(
        code='STORAGE_001',
        message=MSG_STORAGE_001,
        error_type=ErrorType.INFRASTRUCTURE,
        http_status=503,
    ),
    'STORAGE_UPLOAD_FAILED': ErrorCode(
        code='STORAGE_002',
        message=MSG_STORAGE_001,
        error_type=ErrorType.INFRASTRUCTURE,
        http_status=503,
    ),
    'STORAGE_DOWNLOAD_FAILED': ErrorCode(
        code='STORAGE_003',
        message=MSG_STORAGE_003,
        error_type=ErrorType.INFRASTRUCTURE,
        http_status=503,
    ),
    'STORAGE_BUCKET_CREATE_FAILED': ErrorCode(
        code='STORAGE_004',
        message=MSG_STORAGE_005,
        error_type=ErrorType.INFRASTRUCTURE,
        http_status=503,
    ),
    'STORAGE_FILE_NOT_FOUND': ErrorCode(
        code='STORAGE_005',
        message=MSG_STORAGE_007,
        error_type=ErrorType.INFRASTRUCTURE,
        http_status=404,
    ),
}

# Authentication error codes
AUTH_ERROR_CODES = {
    'AUTHENTICATION_FAILED': ErrorCode(
        code='AUTH_001',
        message=MSG_AUTH_001,
        error_type=ErrorType.AUTHENTICATION,
        http_status=401,
    ),
}

# Permission error codes
PERMISSION_ERROR_CODES = {
    'PERMISSION_DENIED': ErrorCode(
        code='PERM_001',
        message=MSG_PERM_001,
        error_type=ErrorType.AUTHORIZATION,
        http_status=403,
    ),
}

# Database error codes
DATABASE_ERROR_CODES = {
    'DATABASE_CONNECTION_ERROR': ErrorCode(
        code='DB_001',
        message=MSG_DB_001,
        error_type=ErrorType.INFRASTRUCTURE,
        http_status=503,
    ),
    'DATABASE_OPERATION_ERROR': ErrorCode(
        code='DB_002',
        message=MSG_DB_003,
        error_type=ErrorType.INFRASTRUCTURE,
        http_status=500,
    ),
    'DATABASE_CONSTRAINT_ERROR': ErrorCode(
        code='DB_004',
        message=MSG_DB_007,
        error_type=ErrorType.DOMAIN,
        http_status=409,
    ),
}

# External service error codes
EXTERNAL_SERVICE_ERROR_CODES = {
    'REDIS_CONNECTION_ERROR': ErrorCode(
        code='EXT_001',
        message=MSG_EXT_001,
        error_type=ErrorType.EXTERNAL_SERVICE,
        http_status=503,
    ),
    'REDIS_OPERATION_ERROR': ErrorCode(
        code='EXT_002',
        message=MSG_EXT_003,
        error_type=ErrorType.EXTERNAL_SERVICE,
        http_status=500,
    ),
    'HTTP_CLIENT_ERROR': ErrorCode(
        code='EXT_003',
        message=MSG_EXT_005,
        error_type=ErrorType.EXTERNAL_SERVICE,
        http_status=502,
    ),
    'HTTP_TIMEOUT_ERROR': ErrorCode(
        code='EXT_004',
        message=MSG_EXT_007,
        error_type=ErrorType.EXTERNAL_SERVICE,
        http_status=504,
    ),
}

# Validation error codes
VALIDATION_ERROR_CODES = {
    'INVALID_FILE_SIZE': ErrorCode(
        code='VAL_001',
        message=MSG_VAL_001,
        error_type=ErrorType.VALIDATION,
        http_status=400,
    ),
}

# Infrastructure error codes
INFRA_ERROR_CODES = {
    'INTERNAL_SERVER_ERROR': ErrorCode(
        code='INFRA_005',
        message='Internal server error',
        error_type=ErrorType.INTERNAL,
        http_status=500,
    ),
}
