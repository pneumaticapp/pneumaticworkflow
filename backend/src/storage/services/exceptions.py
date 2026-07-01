from src.generics.exceptions import BaseServiceException
from src.storage import messages as fs_messages


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
