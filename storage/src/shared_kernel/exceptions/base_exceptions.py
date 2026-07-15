"""Base exception classes."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ErrorType(StrEnum):
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
    """Standard error response.

    Format is unified with the Django/DRF backend:
    {code, message, details?: {reason: str}}
    """

    code: str
    message: str
    details: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns backend-compatible format:
        - code: error code string (e.g. 'FILE_001')
        - message: human-readable message
        - details: optional dict with 'reason' key
        """
        result: dict[str, Any] = {
            'code': self.code,
            'message': self.message,
        }
        if self.details:
            result['details'] = {'reason': self.details}
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

    def to_response(self) -> ErrorResponse:
        """Convert to error response."""
        return ErrorResponse(
            code=self.error_code.code,
            message=self.error_code.message,
            details=self.details,
        )

    def __str__(self) -> str:
        """Return string representation."""
        return f'{self.error_code.code}: {self.error_code.message}'
