from django.utils.functional import Promise
from rest_framework.exceptions import ValidationError

from src.generics.entities import ValidationErrorData
from src.generics.exceptions import BaseServiceException
from src.storage import messages as fs_messages
from src.utils.validation import ErrorCode


class FileServiceException(BaseServiceException):

    pass


class FileUploadException(FileServiceException):

    default_message = fs_messages.MSG_FS_0007


class FileUploadInvalidResponseException(FileServiceException):

    default_message = fs_messages.MSG_FS_0008


class FileUploadParseErrorException(FileServiceException):

    default_message = fs_messages.MSG_FS_0009


class FileUploadNoFileIdException(FileServiceException):

    default_message = fs_messages.MSG_FS_0010


class FileServiceConnectionException(FileServiceException):

    default_message = fs_messages.MSG_FS_0001


class FileServiceConnectionFailedException(FileServiceException):

    default_message = fs_messages.MSG_FS_0002


class FileServiceAuthException(FileServiceException):

    default_message = fs_messages.MSG_FS_0003


class FileServiceAuthFailedException(FileServiceException):

    default_message = fs_messages.MSG_FS_0004


class FileSizeExceededException(FileServiceException):

    default_message = fs_messages.MSG_FS_0005


class InvalidFileTypeException(FileServiceException):

    default_message = fs_messages.MSG_FS_0006


class StorageUnavailable(Exception):
    pass


class UploadConflict(ValidationError):
    status_code = 409

    def __init__(self, message: str | Promise):
        super().__init__(
            detail=ValidationErrorData(
                message=message,
                code=ErrorCode.VALIDATION_ERROR,
                details={},
            ),
        )


class IneligibleCleanup(Exception):
    """Storage gets `{'eligible': false}` and keeps the file."""
