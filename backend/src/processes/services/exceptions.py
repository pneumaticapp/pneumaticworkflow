from src.generics.exceptions import BaseServiceException
from src.processes.messages import template as pt_messages
from src.processes.messages import workflow as pw_messages


class PublicIdCreateMaxDeepException(BaseServiceException):

    default_message = pt_messages.MSG_PT_0025


class EmbedIdCreateMaxDeepException(BaseServiceException):

    default_message = pt_messages.MSG_PT_0026


class WorkflowActionServiceException(BaseServiceException):

    pass


class ResumeCompletedWorkflow(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0017


class DelayedWorkflowCannotBeChanged(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0072


class CompletedWorkflowCannotBeChanged(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0017


class BlockedBySubWorkflows(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0071


class FirstTaskCannotBeReverted(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0078


class RevertToSkippedTask(WorkflowActionServiceException):

    pass


class ReturnToFutureTask(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0081


class RevertInactiveTask(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0086


class CompleteDelayedWorkflow(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0004


class CompleteCompletedWorkflow(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0008


class CompleteInactiveTask(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0086


class UserNotPerformer(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0087


class UserAlreadyCompleteTask(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0007


class ChecklistIncompleted(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0006


class SubWorkflowsIncompleted(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0070


class CompletedTaskCannotBeReturned(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0088


class PermissionDenied(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0011


class AttachmentServiceException(BaseServiceException):

    pass


class CloudServiceException(AttachmentServiceException):

    default_message = pw_messages.MSG_PW_0040


class AttachmentEmptyBlobException(AttachmentServiceException):

    default_message = pw_messages.MSG_PW_0041


class OpenAiServiceException(BaseServiceException):

    pass


class OpenAiServiceUnavailable(OpenAiServiceException):

    default_message = pw_messages.MSG_PW_0042


class OpenAiServiceFailed(OpenAiServiceException):

    default_message = pw_messages.MSG_PW_0043


class OpenAiLimitTemplateGenerations(OpenAiServiceException):

    default_message = pw_messages.MSG_PW_0044


class OpenAiTemplateStepsNotExist(OpenAiServiceException):

    default_message = pw_messages.MSG_PW_0045


class OpenAiStepsPromptNotExist(OpenAiServiceException):

    default_message = pw_messages.MSG_PW_0046


class TemplateServiceException(BaseServiceException):

    pass


class CommentServiceException(BaseServiceException):

    pass


class AttachmentNotFound(CommentServiceException):

    default_message = pw_messages.MSG_PW_0037


class CommentTextRequired(CommentServiceException):

    default_message = pw_messages.MSG_PW_0047


class CommentedWorkflowNotRunning(CommentServiceException):

    default_message = pw_messages.MSG_PW_0048


class CommentIsDeleted(CommentServiceException):

    default_message = pw_messages.MSG_PW_0049


class WorkflowServiceException(BaseServiceException):

    pass


class CommentedTaskNotActive(CommentServiceException):

    default_message = pw_messages.MSG_PW_0089


class CommentedNotTask(CommentServiceException):

    default_message = pw_messages.MSG_PW_0077
