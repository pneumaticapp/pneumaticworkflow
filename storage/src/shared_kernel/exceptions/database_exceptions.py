"""Database exceptions"""

from typing import Any, Optional

from .base_exceptions import BaseAppException
from .error_codes import DATABASE_ERROR_CODES
from .error_messages import (
    MSG_DB_004,
    MSG_DB_008,
)


class DatabaseError(BaseAppException):
    """Base database error"""

    def __init__(
        self,
        error_code_key: str,
        details: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        error_code = DATABASE_ERROR_CODES[error_code_key]
        super().__init__(error_code, details, **kwargs)


class DatabaseConnectionError(DatabaseError):
    """Database connection error"""

    def __init__(
        self,
        details: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__('DATABASE_CONNECTION_ERROR', details, **kwargs)


class DatabaseOperationError(DatabaseError):
    """Database operation error"""

    def __init__(
        self,
        operation: str,
        details: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        custom_details = MSG_DB_004.format(operation=operation)
        if details:
            custom_details += f': {details}'
        super().__init__('DATABASE_OPERATION_ERROR', custom_details, **kwargs)


class DatabaseTransactionError(DatabaseError):
    """Database transaction error"""

    def __init__(
        self,
        details: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__('DATABASE_TRANSACTION_ERROR', details, **kwargs)


class DatabaseConstraintError(DatabaseError):
    """Database constraint error"""

    def __init__(
        self,
        constraint: str,
        details: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        custom_details = MSG_DB_008.format(
            constraint=constraint, details=details or 'Unknown error'
        )
        super().__init__('DATABASE_CONSTRAINT_ERROR', custom_details, **kwargs)
