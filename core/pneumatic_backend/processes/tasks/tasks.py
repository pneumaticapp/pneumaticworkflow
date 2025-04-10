# pylint: disable=broad-except, cell-var-from-loop

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models import F
from pneumatic_backend.processes.enums import WorkflowStatus, TaskStatus
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService,
)
from pneumatic_backend.processes.models import (
    Task,
)

UserModel = get_user_model()


@shared_task
def complete_tasks(
    user_id: int,
    is_superuser: bool,
    auth_type: AuthTokenType.LITERALS
):

    """ Complete all tasks for specific user where completion_by_all is True
        and the only one performer already complete the task

        Use after deletion task performer """

    user = UserModel.objects.get(id=user_id)
    tasks = (
        Task.objects.filter(
            status=TaskStatus.ACTIVE,
            require_completion_by_all=True,
            taskperformer__user_id=user_id,
            number=F('workflow__current_task'),
            workflow__status=WorkflowStatus.RUNNING
        )
        .select_related('workflow')
        .exclude(taskperformer__is_completed=False)
        .exclude_directly_deleted().prefetch_related('performers')
    )
    for task in tasks:
        service = WorkflowActionService(
            workflow=task.workflow,
            user=user,
            is_superuser=is_superuser,
            auth_type=auth_type
        )
        service.complete_task(task)
