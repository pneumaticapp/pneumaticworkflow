from src.generics.exceptions import BaseServiceException
from src.payment.messages import MSG_BL_0022


class AccountServiceException(BaseServiceException):
    pass


class DowngradeException(AccountServiceException):

    default_message = MSG_BL_0022
