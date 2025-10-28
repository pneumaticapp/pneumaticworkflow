"""Authentication exceptions."""

from .base_exceptions import BaseAppError
from .error_codes import AUTH_ERROR_CODES


class AuthenticationError(BaseAppError):
    """Authentication error."""

    def __init__(
        self,
        details: str | None = None,
        **kwargs: str | int | None,
    ) -> None:
        """Initialize authentication error.

        Args:
            details: Optional error details.
            **kwargs: Additional error parameters.

        """
        error_code = AUTH_ERROR_CODES['AUTHENTICATION_FAILED']
        super().__init__(error_code, details, **kwargs)


class TokenExpiredError(AuthenticationError):
    """Token expired error."""

    def __init__(self, details: str | None = None) -> None:
        """Initialize token expired error.

        Args:
            details: Optional error details.

        """
        super().__init__(details)
        # Override error_code for this specific exception
        self.error_code = AUTH_ERROR_CODES['TOKEN_EXPIRED']


class InvalidTokenError(AuthenticationError):
    """Invalid token error."""

    def __init__(self, details: str | None = None) -> None:
        """Initialize invalid token error.

        Args:
            details: Optional error details.

        """
        super().__init__(details)
        # Override error_code for this specific exception
        self.error_code = AUTH_ERROR_CODES['INVALID_TOKEN']


class TokenIdentificationError(AuthenticationError):
    """Token identification error."""

    def __init__(self, details: str | None = None) -> None:
        """Initialize token identification error.

        Args:
            details: Optional error details.

        """
        super().__init__(details)
        # Override error_code for this specific exception
        self.error_code = AUTH_ERROR_CODES['TOKEN_IDENTIFICATION_ERROR']


class MissingAccountIdError(AuthenticationError):
    """Missing account ID error."""

    def __init__(self, details: str | None = None) -> None:
        """Initialize missing account ID error.

        Args:
            details: Optional error details.

        """
        super().__init__(details)
        # Override error_code for this specific exception
        self.error_code = AUTH_ERROR_CODES['MISSING_ACCOUNT_ID']
