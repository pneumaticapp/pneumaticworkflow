from typing import Optional
from pneumatic_backend.generics.exceptions import BaseServiceException
from pneumatic_backend.authentication.messages import (
    MSG_AU_0001,
    MSG_AU_0004,
    MSG_AU_0005,
    MSG_AU_0008,
    MSG_AU_0009,
)


class AuthException(BaseServiceException):

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[dict] = None
    ):
        self.details = details
        super().__init__(message)


class TokenInvalidOrExpired(AuthException):

    default_message = MSG_AU_0009


class AccessTokenNotFound(AuthException):

    default_message = MSG_AU_0001


class EmailNotExist(AuthException):

    default_message = MSG_AU_0004


class GraphApiRequestError(AuthException):

    default_message = MSG_AU_0005


class AuthenticationFailed(BaseServiceException):

    default_message = MSG_AU_0008
