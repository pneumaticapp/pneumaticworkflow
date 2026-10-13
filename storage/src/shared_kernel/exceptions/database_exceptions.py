"""Database exceptions."""

from .base_exceptions import BaseAppError
from .error_codes import DATABASE_ERROR_CODES
from .error_messages import (
    MSG_DB_004,
    MSG_DB_008,
)


class DatabaseError(BaseAppError):
    """Base database error."""

    def __init__(
        self,
        error_code_key: str,
        details: str | None = None,
        **kwargs: str | int | None,
    ) -> None:
        """Initialize database error.

        Args:
            error_code_key: Error code key from DATABASE_ERROR_CODES.
            details: Optional error details.
            **kwargs: Additional error parameters.

        """
        error_code = DATABASE_ERROR_CODES[error_code_key]
        super().__init__(error_code, details, **kwargs)


class DatabaseConnectionError(DatabaseError):
    """Database connection error."""

    def __init__(
        self,
        details: str | None = None,
        **kwargs: str | int | None,
    ) -> None:
        """Initialize database connection error.

        Args:
            details: Optional error details.
            **kwargs: Additional error parameters.

        """
        super().__init__('DATABASE_CONNECTION_ERROR', details, **kwargs)


class DatabaseOperationError(DatabaseError):
    """Database operation error."""

    def __init__(
        self,
        operation: str,
        details: str | None = None,
        **kwargs: str | int | None,
    ) -> None:
        """Initialize database operation error.

        Args:
            operation: Name of the failed operation.
            details: Optional error details.
            **kwargs: Additional error parameters.

        """
        custom_details = MSG_DB_004.format(
            operation=operation,
            details=details or 'Unknown error',
        )
        super().__init__('DATABASE_OPERATION_ERROR', custom_details, **kwargs)


class DatabaseConstraintError(DatabaseError):
    """Database constraint error."""

    def __init__(
        self,
        constraint: str,
        details: str | None = None,
        **kwargs: str | int | None,
    ) -> None:
        """Initialize database constraint error.

        Args:
            constraint: Name of the violated constraint.
            details: Optional error details.
            **kwargs: Additional error parameters.

        """
        custom_details = MSG_DB_008.format(
            constraint=constraint,
            details=details or 'Unknown error',
        )
        super().__init__('DATABASE_CONSTRAINT_ERROR', custom_details, **kwargs)
