"""Universal exception handler."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.responses import Response
from starlette.status import HTTP_401_UNAUTHORIZED

from src.shared_kernel.browser_utils import (
    is_browser_navigation,
    redirect_to_error_page,
    redirect_to_login,
)
from src.shared_kernel.config import get_settings
from src.shared_kernel.exceptions.base_exceptions import (
    BaseAppError,
    ErrorResponse,
    ErrorType,
)
from src.shared_kernel.exceptions.error_codes import (
    INFRA_ERROR_CODES,
    VALIDATION_ERROR_CODES,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register universal exception handlers."""
    # Error types whose details may contain sensitive internals
    # (SQL queries, S3 paths, Redis keys) and must be hidden
    # from clients in production.
    sensitive_error_types = frozenset(
        {
            ErrorType.INFRASTRUCTURE,
            ErrorType.EXTERNAL_SERVICE,
            ErrorType.INTERNAL,
        }
    )

    @app.exception_handler(BaseAppError)
    async def base_app_exception_handler(
        request: Request,
        exc: BaseAppError,
    ) -> Response:
        """Handle base application exceptions."""
        # Log full details (always, regardless of mode)
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

        # Browser navigation gets redirect instead of JSON
        if is_browser_navigation(request):
            if exc.http_status == HTTP_401_UNAUTHORIZED:
                return redirect_to_login(request)
            return redirect_to_error_page()

        # In production, mask details for infrastructure errors
        # to prevent leaking SQL, S3 paths, or Redis keys.
        debug_mode = get_settings().DEBUG
        details = exc.details
        if not debug_mode and exc.error_type in sensitive_error_types:
            details = None

        # Create error response
        error_response = exc.to_response()
        # Override details after to_response (which uses exc.details)
        error_response.details = details

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
            code=error_code.code,
            message=error_code.message,
            details=details,
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
            code=error_code.code,
            message=error_code.message,
            details=details,
        )

        return JSONResponse(
            status_code=error_code.http_status,
            content=error_response.to_dict(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception,
    ) -> Response:
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

        # Browser navigation gets redirect to error page
        if is_browser_navigation(request):
            return redirect_to_error_page()

        # Check debug mode
        debug_mode = get_settings().DEBUG

        error_response = ErrorResponse(
            code=error_code.code,
            message=error_code.message,
            details=str(exc) if debug_mode else None,
        )

        return JSONResponse(
            status_code=error_code.http_status,
            content=error_response.to_dict(),
        )
