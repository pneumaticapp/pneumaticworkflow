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


class AIHandlerException(AIServiceException):

    pass


class AIProviderException(AIServiceException):

    pass


class AIAgentException(AIServiceException):

    pass


class AIProviderConnectionException(AIHandlerException):

    default_message = MSG_AI_0001


class AIProviderRequestFailedException(AIHandlerException):

    default_message = MSG_AI_0002


class AIProviderInvalidResponseException(AIHandlerException):

    default_message = MSG_AI_0003


class AIAgentNameNotUniqueException(AIAgentException):

    default_message = MSG_AI_0004


class AIProviderInUseException(AIProviderException):

    default_message = MSG_AI_0005
