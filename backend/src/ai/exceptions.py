from src.ai.messages import (
    MSG_AI_0001,
    MSG_AI_0002,
    MSG_AI_0003,
    MSG_AI_0004,
    MSG_AI_0005,
    MSG_AI_0014,
    MSG_AI_0016,
    MSG_AI_0017,
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


class AIHandlerConnectionException(AIHandlerException):

    default_message = MSG_AI_0001


class AIHandlerRequestFailed(AIHandlerException):

    default_message = MSG_AI_0002


class AIHandlerUnauthorized(AIHandlerException):

    def __init__(self, error: str):
        super().__init__(message=MSG_AI_0016(error=error))


class AIHandlerPermissionDenied(AIHandlerException):

    def __init__(self, error: str):
        super().__init__(message=MSG_AI_0017(error=error))


class AIHandlerInvalidResponse(AIHandlerException):

    default_message = MSG_AI_0003


class AIAgentNameNotUniqueException(AIAgentException):

    default_message = MSG_AI_0004


class AIProviderInUseException(AIProviderException):

    default_message = MSG_AI_0005


class AIProviderModelsNotResponded(AIProviderException):

    default_message = MSG_AI_0014


class AIAgentAttemptsExceededException(AIAgentException):

    pass
