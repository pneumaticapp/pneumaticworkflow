from pneumatic_backend.generics.exceptions import BaseServiceException
from pneumatic_backend.analytics.messages import MSG_AS_0001


class AnalyticServiceException(BaseServiceException):
    pass


class InvalidUserCredentials(AnalyticServiceException):

    default_message = MSG_AS_0001
