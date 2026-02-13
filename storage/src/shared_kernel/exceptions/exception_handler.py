"""Universal exception handler."""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.shared_kernel.exceptions.base_exceptions import (
    BaseAppError,
    ErrorResponse,
)
from src.shared_kernel.exceptions.error_codes import (
    INFRA_ERROR_CODES,
    VALIDATION_ERROR_CODES,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register universal exception handlers."""

    @app.exception_handler(BaseAppError)
    async def base_app_exception_handler(
        request: Request,
        exc: BaseAppError,
    ) -> JSONResponse:
        """Handle base application exceptions."""
        # Log error
        logger.error(
            'Application exception: %s - %s',
            exc.error_code.code,
            exc.error_code.message,
            extra={
                'error_code': exc.error_code.code,
                'error_type': exc.error_type.value,
                'details': exc.details,
                'request_path': request.url.path,
                'request_method': request.method,
            },
        )

        # Create error response
        error_response = exc.to_response(
            timestamp=datetime.now(tz=UTC).isoformat(),
            request_id=getattr(request.state, 'request_id', None),
        )

        return JSONResponse(
            status_code=exc.http_status,
            content=error_response.to_dict(),
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle FastAPI request body/query/path validation errors."""
        error_code = VALIDATION_ERROR_CODES['MISSING_REQUIRED_FIELD']
        details = str(exc.errors())

        logger.warning(
            'Request validation error: %s',
            details,
            extra={
                'error_code': error_code.code,
                'request_path': request.url.path,
                'request_method': request.method,
            },
        )

        error_response = ErrorResponse(
            error_code=error_code.code,
            message=error_code.message,
            error_type=error_code.error_type.value,
            details=details,
            timestamp=datetime.now(tz=UTC).isoformat(),
            request_id=getattr(request.state, 'request_id', None),
        )

        return JSONResponse(
            status_code=error_code.http_status,
            content=error_response.to_dict(),
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        error_code = VALIDATION_ERROR_CODES['MISSING_REQUIRED_FIELD']
        details = str(exc.errors())

        logger.warning(
            'Validation error: %s',
            details,
            extra={
                'error_code': error_code.code,
                'request_path': request.url.path,
                'request_method': request.method,
            },
        )

        error_response = ErrorResponse(
            error_code=error_code.code,
            message=error_code.message,
            error_type=error_code.error_type.value,
            details=details,
            timestamp=datetime.now(tz=UTC).isoformat(),
            request_id=getattr(request.state, 'request_id', None),
        )

        return JSONResponse(
            status_code=error_code.http_status,
            content=error_response.to_dict(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle general exceptions."""
        error_code = INFRA_ERROR_CODES['INTERNAL_SERVER_ERROR']

        # Log unexpected error
        logger.error(
            'Unexpected error: %s',
            exc,
            extra={
                'error_code': error_code.code,
                'request_path': request.url.path,
                'request_method': request.method,
            },
        )

        # Check debug mode
        debug_mode = getattr(app, 'debug', False)

        error_response = ErrorResponse(
            error_code=error_code.code,
            message=error_code.message,
            error_type=error_code.error_type.value,
            details=str(exc) if debug_mode else None,
            timestamp=datetime.now(tz=UTC).isoformat(),
            request_id=getattr(request.state, 'request_id', None),
        )

        return JSONResponse(
            status_code=error_code.http_status,
            content=error_response.to_dict(),
        )


def create_error_response(
    error_code: str,
    message: str,
    error_type: str,
    details: str | None = None,
    **kwargs: str | int | None,
) -> dict[str, Any]:
    """Create standardized error response."""
    response = {
        'error_code': error_code,
        'message': message,
        'error_type': error_type,
    }

    if details:
        response['details'] = details

    # Convert kwargs values to strings for response
    str_kwargs = {
        key: str(value) if value is not None else None
        for key, value in kwargs.items()
    }
    # Filter out None values for response.update
    filtered_kwargs = {k: v for k, v in str_kwargs.items() if v is not None}
    response.update(filtered_kwargs)

    return response
