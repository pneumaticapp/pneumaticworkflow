from src.processes.messages.workflow import (
    MSG_PW_0058,
)
from src.generics.exceptions import (
    BaseServiceException,
    BaseApiNameException,
)


class PerformersServiceException(BaseServiceException):

    pass


class ChecklistServiceException(BaseServiceException):

    pass


class ChecklistSelectionNotFound(ChecklistServiceException):

    default_message = MSG_PW_0058


class TaskFieldException(BaseApiNameException):

    pass


class TaskServiceException(BaseServiceException):

    pass


class GroupPerformerServiceException(BaseServiceException):

    pass
