from src.ai.messages import (
    MSG_AI_0001,
    MSG_AI_0002,
    MSG_AI_0003,
    MSG_AI_0004,
    MSG_AI_0005,
)
from src.generics.exceptions import BaseServiceException


class AIServiceException(BaseServiceException):

    pass


class AIProviderConnectionException(AIServiceException):

    default_message = MSG_AI_0001


class AIProviderRequestFailedException(AIServiceException):

    default_message = MSG_AI_0002


class AIProviderInvalidResponseException(AIServiceException):

    default_message = MSG_AI_0003


class AIAgentNameNotUniqueException(AIServiceException):

    default_message = MSG_AI_0004


class AIProviderInUseException(AIServiceException):

    default_message = MSG_AI_0005
