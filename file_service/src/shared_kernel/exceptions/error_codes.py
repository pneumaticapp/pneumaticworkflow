"""Error codes catalog"""

from .base_exceptions import ErrorCode, ErrorType
from .error_messages import (
    MSG_AUTH_001,
    MSG_AUTH_003,
    MSG_AUTH_005,
    MSG_AUTH_007,
    MSG_AUTH_009,
    MSG_DB_001,
    MSG_DB_003,
    MSG_DB_005,
    MSG_DB_007,
    MSG_EXT_001,
    MSG_EXT_003,
    MSG_EXT_005,
    MSG_EXT_007,
    MSG_EXT_009,
    MSG_FILE_001,
    MSG_FILE_004,
    MSG_FILE_006,
    MSG_FILE_008,
    MSG_PERM_001,
    MSG_PERM_002,
    MSG_STORAGE_001,
    MSG_STORAGE_003,
    MSG_STORAGE_005,
    MSG_STORAGE_007,
    MSG_VAL_001,
    MSG_VAL_003,
    MSG_VAL_005,
    MSG_VAL_007,
    MSG_VAL_009,
    MSG_VAL_011,
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
    'FILE_ALREADY_EXISTS': ErrorCode(
        code='FILE_004',
        message=MSG_FILE_008,
        error_type=ErrorType.DOMAIN,
        http_status=409,
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
    'TOKEN_EXPIRED': ErrorCode(
        code='AUTH_002',
        message=MSG_AUTH_003,
        error_type=ErrorType.AUTHENTICATION,
        http_status=401,
    ),
    'INVALID_TOKEN': ErrorCode(
        code='AUTH_003',
        message=MSG_AUTH_005,
        error_type=ErrorType.AUTHENTICATION,
        http_status=401,
    ),
    'TOKEN_IDENTIFICATION_ERROR': ErrorCode(
        code='AUTH_004',
        message=MSG_AUTH_007,
        error_type=ErrorType.AUTHENTICATION,
        http_status=401,
    ),
    'MISSING_ACCOUNT_ID': ErrorCode(
        code='AUTH_005',
        message=MSG_AUTH_009,
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
    'ACCESS_DENIED_PUBLIC_TOKEN': ErrorCode(
        code='PERM_002',
        message=MSG_PERM_002,
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
    'DATABASE_TRANSACTION_ERROR': ErrorCode(
        code='DB_003',
        message=MSG_DB_005,
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
    'EXTERNAL_SERVICE_UNAVAILABLE': ErrorCode(
        code='EXT_005',
        message=MSG_EXT_009,
        error_type=ErrorType.EXTERNAL_SERVICE,
        http_status=503,
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
    'INVALID_FILE_TYPE': ErrorCode(
        code='VAL_002',
        message=MSG_VAL_003,
        error_type=ErrorType.VALIDATION,
        http_status=400,
    ),
    'INVALID_TOKEN_FORMAT': ErrorCode(
        code='VAL_003',
        message=MSG_VAL_005,
        error_type=ErrorType.VALIDATION,
        http_status=400,
    ),
    'MISSING_REQUIRED_FIELD': ErrorCode(
        code='VAL_004',
        message=MSG_VAL_007,
        error_type=ErrorType.VALIDATION,
        http_status=400,
    ),
    'INVALID_INPUT_FORMAT': ErrorCode(
        code='VAL_005',
        message=MSG_VAL_009,
        error_type=ErrorType.VALIDATION,
        http_status=400,
    ),
    'VALIDATION_FAILED': ErrorCode(
        code='VAL_006',
        message=MSG_VAL_011,
        error_type=ErrorType.VALIDATION,
        http_status=400,
    ),
}

# Infrastructure error codes
INFRA_ERROR_CODES = {
    'DATABASE_CONNECTION_ERROR': ErrorCode(
        code='INFRA_001',
        message='Database connection error',
        error_type=ErrorType.INFRASTRUCTURE,
        http_status=503,
    ),
    'DATABASE_OPERATION_FAILED': ErrorCode(
        code='INFRA_002',
        message='Database operation failed',
        error_type=ErrorType.INFRASTRUCTURE,
        http_status=503,
    ),
    'REDIS_CONNECTION_ERROR': ErrorCode(
        code='INFRA_003',
        message='Redis connection error',
        error_type=ErrorType.INFRASTRUCTURE,
        http_status=503,
    ),
    'EXTERNAL_SERVICE_ERROR': ErrorCode(
        code='INFRA_004',
        message='External service error',
        error_type=ErrorType.EXTERNAL_SERVICE,
        http_status=503,
    ),
    'INTERNAL_SERVER_ERROR': ErrorCode(
        code='INFRA_005',
        message='Internal server error',
        error_type=ErrorType.INTERNAL,
        http_status=500,
    ),
}
