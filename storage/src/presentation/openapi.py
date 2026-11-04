"""Documentation contracts for the Files API, without runtime changes."""

from typing import Any

from pydantic import BaseModel, Field

from src.shared_kernel.exceptions.base_exceptions import ErrorCode
from src.shared_kernel.exceptions.error_codes import (
    AUTH_ERROR_CODES,
    DATABASE_ERROR_CODES,
    DOMAIN_ERROR_CODES,
    EXTERNAL_SERVICE_ERROR_CODES,
    INFRA_ERROR_CODES,
    PERMISSION_ERROR_CODES,
    VALIDATION_ERROR_CODES,
)


class FileErrorDetails(BaseModel):
    """Optional reason emitted by the application exception handlers."""

    reason: str


class FileErrorResponse(BaseModel):
    """Application error; sensitive infrastructure details may be omitted."""

    code: str
    message: str
    details: FileErrorDetails | None = Field(default=None)


class FileRateLimitResponse(BaseModel):
    """Rate-limit middleware response, distinct from application errors."""

    detail: str
    retry_after: int


FILES_SECURITY_SCHEMES: dict[str, dict[str, str]] = {
    'tokenAuth': {
        'type': 'http',
        'scheme': 'bearer',
        'description': 'User API key or session token: Bearer <token>.',
    },
    'filesGuestAuth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-Guest-Authorization',
        'description': 'Guest task JWT, without a Bearer prefix.',
    },
    'filesPublicAuth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-Public-Authorization',
        'description': 'Public or embed template token: Token <token>.',
    },
    'filesSessionCookieAuth': {
        'type': 'apiKey',
        'in': 'cookie',
        'name': 'file_service_auth',
        'description': 'User API key or session token, without a prefix.',
    },
    'filesTokenCookieAuth': {
        'type': 'apiKey',
        'in': 'cookie',
        'name': 'token',
        'description': 'User API key or session token, without a prefix.',
    },
    'filesGuestCookieAuth': {
        'type': 'apiKey',
        'in': 'cookie',
        'name': 'guest-token',
        'description': 'Guest task JWT, without a prefix.',
    },
    'filesPublicCookieAuth': {
        'type': 'apiKey',
        'in': 'cookie',
        'name': 'public-token',
        'description': 'Public or embed template token: Token <token>.',
    },
}

FILES_SECURITY: list[dict[str, list[str]]] = [
    {name: []} for name in FILES_SECURITY_SCHEMES
]

DOWNLOAD_HEADERS = {
    'Content-Disposition': {
        'description': 'Attachment with a UTF-8 percent-encoded filename.',
        'schema': {'type': 'string'},
        'example': "attachment; filename*=utf-8''report.pdf",
    },
    'Accept-Ranges': {
        'description': 'Supported range unit.',
        'schema': {'type': 'string', 'enum': ['bytes']},
    },
    'Content-Length': {
        'description': 'Number of bytes in this response.',
        'schema': {'type': 'integer', 'minimum': 0},
    },
    'X-Content-Type-Options': {
        'description': 'Prevents browser MIME type sniffing.',
        'schema': {'type': 'string', 'enum': ['nosniff']},
    },
}

CONTENT_RANGE_HEADER = {
    'description': (
        'Selected byte range and total size, or bytes */<size> for 416.'
    ),
    'schema': {'type': 'string'},
    'example': 'bytes 0-1023/2048',
}

BINARY_CONTENT = {
    '*/*': {
        'schema': {'type': 'string', 'format': 'binary'},
    },
}


def _error_response(
    error: ErrorCode,
    description: str,
) -> dict[str, Any]:
    """Describe the same public fields as ErrorResponse.to_dict()."""
    return {
        'model': FileErrorResponse,
        'description': description,
        'content': {
            'application/json': {
                'example': {'code': error.code, 'message': error.message},
            },
        },
    }


COMMON_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: _error_response(
        AUTH_ERROR_CODES['AUTHENTICATION_FAILED'],
        'No valid user, guest, public, or embed credential was provided.',
    ),
    403: _error_response(
        PERMISSION_ERROR_CODES['PERMISSION_DENIED'],
        'The authenticated credential does not have access.',
    ),
    422: _error_response(
        VALIDATION_ERROR_CODES['MISSING_REQUIRED_FIELD'],
        'Invalid path/header/body or missing multipart file. '
        'Optional details.reason contains validation details.',
    ),
    429: {
        'model': FileRateLimitResponse,
        'description': (
            'Per-client-IP sliding-window rate limit exceeded, when enabled. '
            'Wait Retry-After seconds before retrying.'
        ),
        'headers': {
            'Retry-After': {
                'schema': {'type': 'integer', 'minimum': 0},
                'description': 'Configured rate-limit window, in seconds.',
            },
        },
    },
    500: _error_response(
        INFRA_ERROR_CODES['INTERNAL_SERVER_ERROR'],
        'Unexpected server, database, or Redis operation failure. '
        'Sensitive details are hidden outside debug mode.',
    ),
    503: _error_response(
        DOMAIN_ERROR_CODES['STORAGE_OPERATION_FAILED'],
        'Storage, database, or authentication infrastructure is unavailable.',
    ),
}

UPLOAD_RESPONSES: dict[int | str, dict[str, Any]] = {
    **COMMON_ERROR_RESPONSES,
    409: _error_response(
        DATABASE_ERROR_CODES['DATABASE_CONSTRAINT_ERROR'],
        'The file metadata conflicts with a database constraint.',
    ),
    413: _error_response(
        DOMAIN_ERROR_CODES['FILE_SIZE_EXCEEDED'],
        'File size exceeds the deployment MAX_FILE_SIZE limit in bytes.',
    ),
}

DOWNLOAD_RESPONSES: dict[int | str, dict[str, Any]] = {
    **COMMON_ERROR_RESPONSES,
    200: {
        'description': (
            'Complete file bytes after storage accepts the download. '
            'Content-Type is the stored file MIME type; '
            'The media type range */* describes the binary response.'
        ),
        'content': BINARY_CONTENT,
        'headers': DOWNLOAD_HEADERS,
    },
    206: {
        'description': (
            'Selected bytes when storage accepts the Range request and '
            'the local planner finds it satisfiable against file metadata.'
        ),
        'content': BINARY_CONTENT,
        'headers': {**DOWNLOAD_HEADERS, 'Content-Range': CONTENT_RANGE_HEADER},
    },
    302: {
        'description': (
            'Browser navigation (GET with Accept: text/html) redirects to '
            'sign-in when unauthenticated, or the frontend error page for '
            'handled application/server errors. API requests receive JSON.'
        ),
        'headers': {
            'Location': {'schema': {'type': 'string', 'format': 'uri'}},
        },
    },
    404: _error_response(
        DOMAIN_ERROR_CODES['FILE_NOT_FOUND'],
        'No file metadata or stored file exists for this identifier.',
    ),
    416: {
        'description': (
            'Local planner fallback after storage accepts the stream, when '
            'the range is unsatisfiable against file metadata. The body is '
            'empty. This is not a guaranteed response for invalid ranges: '
            'storage rejection happens earlier and returns 503 STORAGE_003.'
        ),
        'headers': {
            'Content-Range': {
                **CONTENT_RANGE_HEADER,
                'example': 'bytes */2048',
            },
        },
    },
    502: _error_response(
        EXTERNAL_SERVICE_ERROR_CODES['HTTP_CLIENT_ERROR'],
        'The Core backend could not be reached for a file permission check.',
    ),
    504: _error_response(
        EXTERNAL_SERVICE_ERROR_CODES['HTTP_TIMEOUT_ERROR'],
        'The Core backend permission check timed out.',
    ),
    503: _error_response(
        DOMAIN_ERROR_CODES['STORAGE_DOWNLOAD_FAILED'],
        'Storage download failure, including rejected Range headers '
        '(InvalidRange or other storage ClientError). Range is forwarded '
        'unchanged before local 200/206/416 planning. API requests receive '
        'code STORAGE_003 without Content-Range. Database or authentication '
        'infrastructure unavailability may also produce a 503 error.',
    ),
}
