"""Domain exceptions"""

from typing import Any, Optional

from .base_exceptions import BaseAppException
from .error_codes import DOMAIN_ERROR_CODES
from .error_messages import (
    MSG_FILE_002,
    MSG_FILE_003,
    MSG_FILE_005,
    MSG_FILE_007,
    MSG_FILE_009,
    MSG_STORAGE_002,
    MSG_STORAGE_004,
    MSG_STORAGE_006,
    MSG_STORAGE_008,
)


class FileNotFoundError(BaseAppException):
    """File not found error"""

    def __init__(
        self,
        file_id: str,
        account_id: Optional[int] = None,
        details: Optional[str] = None,
    ) -> None:
        error_code = DOMAIN_ERROR_CODES['FILE_NOT_FOUND']
        if account_id:
            message = MSG_FILE_003.format(
                file_id=file_id, account_id=account_id
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
            custom_error_code, details, file_id=file_id, account_id=account_id
        )


class FileAccessDeniedError(BaseAppException):
    """File access denied error"""

    def __init__(
        self,
        file_id: str,
        user_id: int,
        details: Optional[str] = None,
    ) -> None:
        error_code = DOMAIN_ERROR_CODES['FILE_ACCESS_DENIED']
        message = MSG_FILE_005.format(user_id=user_id, file_id=file_id)

        custom_error_code = error_code.__class__(
            code=error_code.code,
            message=message,
            error_type=error_code.error_type,
            http_status=error_code.http_status,
        )

        super().__init__(
            custom_error_code, details, file_id=file_id, user_id=user_id
        )


class FileSizeExceededError(BaseAppException):
    """File size exceeded error"""

    def __init__(
        self,
        size: int,
        max_size: int,
        details: Optional[str] = None,
    ) -> None:
        error_code = DOMAIN_ERROR_CODES['FILE_SIZE_EXCEEDED']
        message = MSG_FILE_007.format(size=size, max_size=max_size)

        custom_error_code = error_code.__class__(
            code=error_code.code,
            message=message,
            error_type=error_code.error_type,
            http_status=error_code.http_status,
        )

        super().__init__(
            custom_error_code, details, size=size, max_size=max_size
        )


class FileAlreadyExistsError(BaseAppException):
    """File already exists error"""

    def __init__(
        self,
        file_id: str,
        details: Optional[str] = None,
    ) -> None:
        error_code = DOMAIN_ERROR_CODES['FILE_ALREADY_EXISTS']
        message = MSG_FILE_009.format(file_id=file_id)

        custom_error_code = error_code.__class__(
            code=error_code.code,
            message=message,
            error_type=error_code.error_type,
            http_status=error_code.http_status,
        )

        super().__init__(custom_error_code, details, file_id=file_id)


class StorageError(BaseAppException):
    """Storage operation error"""

    def __init__(
        self,
        error_code_key: str,
        details: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        error_code = DOMAIN_ERROR_CODES[error_code_key]
        super().__init__(error_code, details, **kwargs)

    @classmethod
    def upload_failed(cls, details: Optional[str] = None) -> 'StorageError':
        """Create upload failed error"""
        custom_details = MSG_STORAGE_002.format(
            details=details or 'Unknown error'
        )
        return cls('STORAGE_UPLOAD_FAILED', custom_details)

    @classmethod
    def download_failed(cls, details: Optional[str] = None) -> 'StorageError':
        """Create download failed error"""
        custom_details = MSG_STORAGE_004.format(
            details=details or 'Unknown error'
        )
        return cls('STORAGE_DOWNLOAD_FAILED', custom_details)

    @classmethod
    def bucket_create_failed(
        cls, details: Optional[str] = None
    ) -> 'StorageError':
        """Create bucket creation failed error"""
        custom_details = MSG_STORAGE_006.format(
            details=details or 'Unknown error'
        )
        return cls('STORAGE_BUCKET_CREATE_FAILED', custom_details)

    @classmethod
    def file_not_found_in_storage(
        cls,
        file_path: str,
        bucket_name: str,
        details: Optional[str] = None,
    ) -> 'StorageError':
        """Create file not found in storage error"""
        custom_details = MSG_STORAGE_008.format(
            file_path=file_path, bucket_name=bucket_name
        )
        if details:
            custom_details += f': {details}'
        return cls('STORAGE_FILE_NOT_FOUND', custom_details)
