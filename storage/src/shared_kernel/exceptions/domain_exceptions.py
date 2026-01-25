"""Domain exceptions."""

from .base_exceptions import BaseAppError
from .error_codes import DOMAIN_ERROR_CODES
from .error_messages import (
    MSG_FILE_002,
    MSG_FILE_003,
    MSG_FILE_005,
    MSG_FILE_007,
    MSG_STORAGE_002,
    MSG_STORAGE_004,
    MSG_STORAGE_006,
    MSG_STORAGE_008,
)


class DomainFileNotFoundError(BaseAppError):
    """File not found error."""

    def __init__(
        self,
        file_id: str,
        account_id: int | None = None,
        details: str | None = None,
    ) -> None:
        """Initialize file not found error.

        Args:
            file_id: ID of the file that was not found.
            account_id: Optional account ID for context.
            details: Optional error details.

        """
        error_code = DOMAIN_ERROR_CODES['FILE_NOT_FOUND']
        if account_id:
            message = MSG_FILE_003.format(
                file_id=file_id,
                account_id=account_id,
            )
        else:
            message = MSG_FILE_002.format(file_id=file_id)

        # Create new ErrorCode with customized message
        custom_error_code = error_code.__class__(
            code=error_code.code,
            message=message,
            error_type=error_code.error_type,
            http_status=error_code.http_status,
        )

        super().__init__(
            custom_error_code,
            details,
            file_id=file_id,
            account_id=account_id,
        )


class FileAccessDeniedError(BaseAppError):
    """File access denied error."""

    def __init__(
        self,
        file_id: str,
        user_id: int,
        details: str | None = None,
    ) -> None:
        """Initialize file access denied error.

        Args:
            file_id: ID of the file access was denied for.
            user_id: ID of the user who was denied access.
            details: Optional error details.

        """
        error_code = DOMAIN_ERROR_CODES['FILE_ACCESS_DENIED']
        message = MSG_FILE_005.format(user_id=user_id, file_id=file_id)

        custom_error_code = error_code.__class__(
            code=error_code.code,
            message=message,
            error_type=error_code.error_type,
            http_status=error_code.http_status,
        )

        super().__init__(
            custom_error_code,
            details,
            file_id=file_id,
            user_id=user_id,
        )


class FileSizeExceededError(BaseAppError):
    """File size exceeded error."""

    def __init__(
        self,
        size: int,
        max_size: int,
        details: str | None = None,
    ) -> None:
        """Initialize file size exceeded error.

        Args:
            size: Actual file size in bytes.
            max_size: Maximum allowed file size in bytes.
            details: Optional error details.

        """
        error_code = DOMAIN_ERROR_CODES['FILE_SIZE_EXCEEDED']
        message = MSG_FILE_007.format(size=size, max_size=max_size)

        custom_error_code = error_code.__class__(
            code=error_code.code,
            message=message,
            error_type=error_code.error_type,
            http_status=error_code.http_status,
        )

        super().__init__(
            custom_error_code,
            details,
            size=size,
            max_size=max_size,
        )


class StorageError(BaseAppError):
    """Storage operation error."""

    def __init__(
        self,
        error_code_key: str,
        details: str | None = None,
        **kwargs: str | int | None,
    ) -> None:
        """Initialize storage operation error.

        Args:
            error_code_key: Error code key from DOMAIN_ERROR_CODES.
            details: Optional error details.
            **kwargs: Additional error parameters.

        """
        error_code = DOMAIN_ERROR_CODES[error_code_key]
        super().__init__(error_code, details, **kwargs)

    @classmethod
    def upload_failed(cls, details: str | None = None) -> 'StorageError':
        """Create upload failed error."""
        custom_details = MSG_STORAGE_002.format(
            details=details or 'Unknown error',
        )
        return cls('STORAGE_UPLOAD_FAILED', custom_details)

    @classmethod
    def download_failed(cls, details: str | None = None) -> 'StorageError':
        """Create download failed error."""
        custom_details = MSG_STORAGE_004.format(
            details=details or 'Unknown error',
        )
        return cls('STORAGE_DOWNLOAD_FAILED', custom_details)

    @classmethod
    def bucket_create_failed(
        cls,
        details: str | None = None,
    ) -> 'StorageError':
        """Create bucket creation failed error."""
        custom_details = MSG_STORAGE_006.format(
            details=details or 'Unknown error',
        )
        return cls('STORAGE_BUCKET_CREATE_FAILED', custom_details)

    @classmethod
    def file_not_found_in_storage(
        cls,
        file_path: str,
        bucket_name: str,
        details: str | None = None,
    ) -> 'StorageError':
        """Create file not found in storage error."""
        custom_details = MSG_STORAGE_008.format(
            file_path=file_path,
            bucket_name=bucket_name,
        )
        if details:
            custom_details += f': {details}'
        return cls('STORAGE_FILE_NOT_FOUND', custom_details)
