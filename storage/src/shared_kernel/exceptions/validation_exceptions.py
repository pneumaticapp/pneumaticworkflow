"""Validation exceptions."""

from .base_exceptions import BaseAppError
from .error_codes import VALIDATION_ERROR_CODES
from .error_messages import (
    MSG_VAL_002,
    MSG_VAL_004,
    MSG_VAL_008,
)


class ValidationError(BaseAppError):
    """Base validation error."""

    def __init__(
        self,
        error_code_key: str,
        details: str | None = None,
        **kwargs: str | int | None,
    ) -> None:
        """Initialize validation error.

        Args:
            error_code_key: Error code key from VALIDATION_ERROR_CODES.
            details: Optional error details.
            **kwargs: Additional error parameters.

        """
        error_code = VALIDATION_ERROR_CODES[error_code_key]
        super().__init__(error_code, details, **kwargs)


class InvalidFileSizeError(ValidationError):
    """Invalid file size error."""

    def __init__(
        self,
        size: int,
        max_size: int,
        details: str | None = None,
        **kwargs: str | int | None,
    ) -> None:
        """Initialize invalid file size error.

        Args:
            size: Actual file size in bytes.
            max_size: Maximum allowed file size in bytes.
            details: Optional error details.
            **kwargs: Additional error parameters.

        """
        custom_details = MSG_VAL_002.format(size=size, max_size=max_size)
        if details:
            custom_details += f': {details}'
        super().__init__('INVALID_FILE_SIZE', custom_details, **kwargs)


class InvalidFileTypeError(ValidationError):
    """Invalid file type error."""

    def __init__(
        self,
        file_type: str,
        allowed_types: list[str],
        details: str | None = None,
        **kwargs: str | int | None,
    ) -> None:
        """Initialize invalid file type error.

        Args:
            file_type: The invalid file type.
            allowed_types: List of allowed file types.
            details: Optional error details.
            **kwargs: Additional error parameters.

        """
        custom_details = MSG_VAL_004.format(
            file_type=file_type,
            allowed_types=', '.join(allowed_types),
        )
        if details:
            custom_details += f': {details}'
        super().__init__('INVALID_FILE_TYPE', custom_details, **kwargs)


class InvalidTokenFormatError(ValidationError):
    """Invalid token format error."""

    def __init__(
        self,
        token_type: str,
        details: str | None = None,
        **kwargs: str | int | None,
    ) -> None:
        """Initialize invalid token format error.

        Args:
            token_type: Type of the invalid token.
            details: Optional error details.
            **kwargs: Additional error parameters.

        """
        custom_details = f'Invalid {token_type} token format'
        if details:
            custom_details += f': {details}'
        super().__init__('INVALID_TOKEN_FORMAT', custom_details, **kwargs)


class MissingRequiredFieldError(ValidationError):
    """Missing required field error."""

    def __init__(
        self,
        field_name: str,
        details: str | None = None,
        **kwargs: str | int | None,
    ) -> None:
        """Initialize missing required field error.

        Args:
            field_name: Name of the missing field.
            details: Optional error details.
            **kwargs: Additional error parameters.

        """
        custom_details = MSG_VAL_008.format(field_name=field_name)
        if details:
            custom_details += f': {details}'
        super().__init__('MISSING_REQUIRED_FIELD', custom_details, **kwargs)


class InvalidInputFormatError(ValidationError):
    """Invalid input format error."""

    def __init__(
        self,
        field_name: str,
        expected_format: str,
        actual_value: str | float | None = None,
        details: str | None = None,
        **kwargs: str | int | None,
    ) -> None:
        """Initialize invalid input format error.

        Args:
            field_name: Name of the field with invalid format.
            expected_format: Expected format description.
            actual_value: Actual value that was provided.
            details: Optional error details.
            **kwargs: Additional error parameters.

        """
        custom_details = (
            f"Field '{field_name}' has invalid format. "
            f'Expected: {expected_format}'
        )
        if actual_value is not None:
            custom_details += f', got: {actual_value}'
        if details:
            custom_details += f': {details}'
        super().__init__('INVALID_INPUT_FORMAT', custom_details, **kwargs)


class ValidationFailedError(ValidationError):
    """General validation failed error."""

    def __init__(
        self,
        validation_errors: list[str],
        details: str | None = None,
        **kwargs: str | int | None,
    ) -> None:
        """Initialize validation failed error.

        Args:
            validation_errors: List of validation error messages.
            details: Optional error details.
            **kwargs: Additional error parameters.

        """
        custom_details = f'Validation failed: {"; ".join(validation_errors)}'
        if details:
            custom_details += f': {details}'
        super().__init__('VALIDATION_FAILED', custom_details, **kwargs)
