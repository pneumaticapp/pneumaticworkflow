from typing import List, Optional

from src.accounts.messages import (
    MSG_A_0004,
    MSG_A_0005,
    MSG_A_0006,
    MSG_A_0007,
    MSG_A_0008,
    MSG_A_0009,
    MSG_A_0010,
    MSG_A_0011,
    MSG_A_0012,
    MSG_A_0013,
    MSG_A_0042,
    MSG_A_0043,
    MSG_A_0044,
)
from src.generics.exceptions import BaseServiceException


class GuestServiceException(BaseServiceException):

    pass


class AccountServiceException(BaseServiceException):

    pass


class UserServiceException(BaseServiceException):

    pass


class AlreadyRegisteredException(UserServiceException):

    default_message = MSG_A_0005


class UsersLimitInvitesException(BaseServiceException):

    default_message = MSG_A_0006


class AlreadyAcceptedInviteException(BaseServiceException):

    default_message = MSG_A_0007

    def __init__(
        self,
        message: Optional[str] = None,
        invites_data: Optional[List[dict]] = None,
    ):
        super().__init__(message)
        self.invites_data = invites_data


class InvalidTransferTokenException(BaseServiceException):

    default_message = MSG_A_0008


class ExpiredTransferTokenException(BaseServiceException):

    default_message = MSG_A_0009


class UserNotFoundException(BaseServiceException):

    default_message = MSG_A_0010


class UserIsPerformerException(BaseServiceException):

    default_message = MSG_A_0011


class ReassignUserDoesNotExist(BaseServiceException):

    default_message = MSG_A_0012


class InvalidOrExpiredToken(BaseServiceException):

    default_message = MSG_A_0013


class UserGroupServiceException(BaseServiceException):

    pass


class ReassignServiceException(BaseServiceException):

    pass


class ReassignUserSameUser(ReassignServiceException):

    default_message = MSG_A_0004


class ReassignUserSameGroup(ReassignServiceException):

    default_message = MSG_A_0042


class ReassignOldUserDoesNotExist(ReassignServiceException):

    default_message = MSG_A_0043


class ReassignNewUserDoesNotExist(ReassignServiceException):

    default_message = MSG_A_0044
