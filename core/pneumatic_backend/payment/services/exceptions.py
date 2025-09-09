from pneumatic_backend.generics.exceptions import BaseServiceException
from pneumatic_backend.payment.messages import MSG_BL_0022


class AccountServiceException(BaseServiceException):
    pass


class DowngradeException(AccountServiceException):

    default_message = MSG_BL_0022
