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


class UserNotPerformer(WorkflowActionServiceException):

    default_message = pw_messages.MSG_PW_0011
