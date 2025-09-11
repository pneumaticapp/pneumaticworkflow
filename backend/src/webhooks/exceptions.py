from src.generics.exceptions import BaseServiceException
from src.webhooks.messages import MSG_WH_0001


class InvalidEventException(BaseServiceException):

    default_message = MSG_WH_0001
