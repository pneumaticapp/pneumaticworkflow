from pneumatic_backend.generics.exceptions import BaseServiceException
from pneumatic_backend.processes.messages import template as pt_messages
from pneumatic_backend.processes.messages import workflow as pw_messages


class PublicIdCreateMaxDeepException(BaseServiceException):

    default_message = pt_messages.MSG_PT_0025


class EmbedIdCreateMaxDeepException(BaseServiceException):

    default_message = pt_messages.MSG_PT_0026


class WorkflowActionServiceException(BaseServiceException):

    pass


class ResumeNotDelayedWorkflow(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0003


class DelayedWorkflowCannotBeChanged(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0072


class CompletedWorkflowCannotBeChanged(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0017


class BlockedBySubWorkflows(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0071


class FirstTaskCannotBeReverted(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0078


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
