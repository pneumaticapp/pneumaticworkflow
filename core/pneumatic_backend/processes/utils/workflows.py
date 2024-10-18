from django.utils import timezone
from pneumatic_backend.processes.enums import WorkflowStatus
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService
)
from pneumatic_backend.processes.models import Delay
from pneumatic_backend.authentication.enums import AuthTokenType
from django.contrib.auth import get_user_model


UserModel = get_user_model()


def resume_delayed_workflows():

    """ Found a workflows with expired delay period and resume them """

    for delay in Delay.objects.filter(
        estimated_end_date__lte=timezone.now(),
        end_date__isnull=True,
        task__workflow__status=WorkflowStatus.DELAYED
    ).prefetch_related(
        'task__workflow__account'
    ):
        workflow = delay.task.workflow
        service = WorkflowActionService(
            user=workflow.account.get_owner(),
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )
        service.resume_workflow(workflow)
