from src.analysis.messages import MSG_AS_0001
from src.generics.exceptions import BaseServiceException


class AnalyticServiceException(BaseServiceException):
    pass


class InvalidUserCredentials(AnalyticServiceException):

    default_message = MSG_AS_0001
