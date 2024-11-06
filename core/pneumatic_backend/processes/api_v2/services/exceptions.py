from pneumatic_backend.generics.exceptions import BaseServiceException
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0037,
    MSG_PW_0040,
    MSG_PW_0041,
    MSG_PW_0042,
    MSG_PW_0043,
    MSG_PW_0044,
    MSG_PW_0045,
    MSG_PW_0046,
    MSG_PW_0047,
    MSG_PW_0048,
    MSG_PW_0049,
)


class AttachmentServiceException(BaseServiceException):

    pass


class CloudServiceException(AttachmentServiceException):

    default_message = MSG_PW_0040


class AttachmentEmptyBlobException(AttachmentServiceException):

    default_message = MSG_PW_0041


class OpenAiServiceException(BaseServiceException):

    pass


class OpenAiServiceUnavailable(OpenAiServiceException):

    default_message = MSG_PW_0042


class OpenAiServiceFailed(OpenAiServiceException):

    default_message = MSG_PW_0043


class OpenAiLimitTemplateGenerations(OpenAiServiceException):

    default_message = MSG_PW_0044


class OpenAiTemplateStepsNotExist(OpenAiServiceException):

    default_message = MSG_PW_0045


class OpenAiStepsPromptNotExist(OpenAiServiceException):

    default_message = MSG_PW_0046


class TemplateServiceException(BaseServiceException):

    pass


class CommentServiceException(BaseServiceException):

    pass


class AttachmentNotFound(CommentServiceException):

    default_message = MSG_PW_0037


class CommentTextRequired(CommentServiceException):

    default_message = MSG_PW_0047


class CommentedWorkflowNotRunning(CommentServiceException):

    default_message = MSG_PW_0048


class CommentIsDeleted(CommentServiceException):

    default_message = MSG_PW_0049


class WorkflowServiceException(BaseServiceException):

    pass
