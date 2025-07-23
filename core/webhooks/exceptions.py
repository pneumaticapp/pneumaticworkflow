from pneumatic_backend.generics.exceptions import BaseServiceException
from pneumatic_backend.webhooks.messages import MSG_WH_0001


class InvalidEventException(BaseServiceException):

    default_message = MSG_WH_0001
