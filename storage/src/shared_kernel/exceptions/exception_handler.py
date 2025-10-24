"""Universal exception handler"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .base_exceptions import BaseAppException, ErrorResponse
from .error_codes import INFRA_ERROR_CODES, VALIDATION_ERROR_CODES

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register universal exception handlers"""

    @app.exception_handler(BaseAppException)
    async def base_app_exception_handler(
        request: Request,
        exc: BaseAppException,
    ) -> JSONResponse:
        """Handle base application exceptions"""

        # Log error
        logger.error(
            f'Application exception: {exc.error_code.code} - '
            f'{exc.error_code.message}',
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
            timestamp=datetime.utcnow().isoformat(),
            request_id=getattr(request.state, 'request_id', None),
        )

        return JSONResponse(
            status_code=exc.http_status,
            content=error_response.to_dict(),
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        """Handle Pydantic validation errors"""

        error_code = VALIDATION_ERROR_CODES['MISSING_REQUIRED_FIELD']
        details = str(exc.errors())

        logger.warning(
            f'Validation error: {details}',
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
            timestamp=datetime.utcnow().isoformat(),
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
        """Handle general exceptions"""

        error_code = INFRA_ERROR_CODES['INTERNAL_SERVER_ERROR']

        # Log unexpected error
        logger.error(
            f'Unexpected error: {str(exc)}',
            exc_info=True,
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
            timestamp=datetime.utcnow().isoformat(),
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
    details: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Create standardized error response"""

    response = {
        'error_code': error_code,
        'message': message,
        'error_type': error_type,
    }

    if details:
        response['details'] = details

    response.update(kwargs)

    return response
