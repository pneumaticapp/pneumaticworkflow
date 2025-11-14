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
