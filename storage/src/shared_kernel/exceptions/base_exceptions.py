"""Base exception classes."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ErrorType(str, Enum):
    """Error types."""

    VALIDATION = 'validation'
    AUTHENTICATION = 'authentication'
    AUTHORIZATION = 'authorization'
    DOMAIN = 'domain'
    INFRASTRUCTURE = 'infrastructure'
    EXTERNAL_SERVICE = 'external_service'
    INTERNAL = 'internal'


@dataclass
class ErrorCode:
    """Error code structure."""

    code: str
    message: str
    error_type: ErrorType
    http_status: int
    details: str | None = None


@dataclass
class ErrorResponse:
    """Standard error response."""

    error_code: str
    message: str
    error_type: str
    details: str | None = None
    timestamp: str | None = None
    request_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'error_code': self.error_code,
            'message': self.message,
            'error_type': self.error_type,
        }
        if self.details:
            result['details'] = self.details
        if self.timestamp:
            result['timestamp'] = self.timestamp
        if self.request_id:
            result['request_id'] = self.request_id
        return result


class BaseAppError(Exception):
    """Base application exception.

    All application exceptions should inherit from this class.
    """

    def __init__(
        self,
        error_code: ErrorCode,
        details: str | None = None,
        **kwargs: str | int | None,
    ) -> None:
        """Initialize base application error.

        Args:
            error_code: Error code instance.
            details: Optional error details.
            **kwargs: Additional error parameters.

        """
        self.error_code = error_code
        self.details = details
        self.kwargs = kwargs
        super().__init__(error_code.message)

    @property
    def http_status(self) -> int:
        """Get HTTP status code."""
        return self.error_code.http_status

    @property
    def error_type(self) -> ErrorType:
        """Get error type."""
        return self.error_code.error_type

    def to_response(self, **kwargs: str | int | None) -> ErrorResponse:
        """Convert to error response."""
        # Convert all kwargs values to strings for ErrorResponse
        str_kwargs = {
            key: str(value) if value is not None else None
            for key, value in kwargs.items()
        }
        return ErrorResponse(
            error_code=self.error_code.code,
            message=self.error_code.message,
            error_type=self.error_type.value,
            details=self.details,
            **str_kwargs,
        )

    def __str__(self) -> str:
        """Return string representation."""
        return f'{self.error_code.code}: {self.error_code.message}'
