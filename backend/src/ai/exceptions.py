from src.ai.messages import MSG_AI_0001, MSG_AI_0002, MSG_AI_0003
from src.generics.exceptions import BaseServiceException


class AIServiceException(BaseServiceException):

    pass


class AIProviderConnectionException(AIServiceException):

    default_message = MSG_AI_0001


class AIProviderRequestFailedException(AIServiceException):

    default_message = MSG_AI_0002


class AIProviderInvalidResponseException(AIServiceException):

    default_message = MSG_AI_0003
