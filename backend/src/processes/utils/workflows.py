from django.contrib.auth import get_user_model
from django.utils import timezone

from src.authentication.enums import AuthTokenType
from src.processes.enums import TaskStatus
from src.processes.models.workflows.task import Delay
from src.processes.services.workflow_action import WorkflowActionService

UserModel = get_user_model()


def resume_delayed_workflows():

    """ Found a tasks with expired delay period and resume them """

    for delay in Delay.objects.filter(
        estimated_end_date__lte=timezone.now(),
        end_date__isnull=True,
        task__status=TaskStatus.DELAYED,
    ).prefetch_related(
        'task__account',
        'task__workflow',
    ):
        workflow = delay.task.workflow
        service = WorkflowActionService(
            workflow=workflow,
            user=workflow.account.get_owner(),
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        service.resume_task(delay.task)
