from celery import shared_task
from django.contrib.auth import get_user_model

from src.accounts.enums import AbsenceStatus
from src.authentication.enums import AuthTokenType
from src.processes.enums import PerformerType, TaskStatus, WorkflowStatus
from src.processes.models.workflows.task import Task, TaskPerformer
from src.processes.models.workflows.workflow import Workflow
from src.processes.services.events import WorkflowEventService
from src.processes.services.workflow_action import (
    WorkflowActionService,
)

UserModel = get_user_model()


@shared_task
def complete_tasks(
    user_id: int,
    is_superuser: bool,
    auth_type: AuthTokenType.LITERALS,
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
            workflow__status=WorkflowStatus.RUNNING,
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
            auth_type=auth_type,
        )
        service.complete_task(task)


@shared_task
def delegate_vacation_tasks():
    """Find active tasks belonging to vacationing users and
    add their substitute group as performer asynchronously.
    """
    vacationing_users = UserModel.objects.filter(
        absence_status__in=[
            AbsenceStatus.VACATION,
            AbsenceStatus.SICK_LEAVE,
        ],
        vacation_schedule__isnull=False,
        vacation_schedule__substitute_group__isnull=False,
    ).select_related('vacation_schedule__substitute_group')

    for user in vacationing_users:
        sub_group = user.vacation_schedule.substitute_group

        # Tasks where user is a performer (ACTIVE/DELAYED)
        user_task_ids = set(
            TaskPerformer.objects.filter(
                user=user,
                type=PerformerType.USER,
                is_completed=False,
                task__status__in=[
                    TaskStatus.ACTIVE,
                    TaskStatus.DELAYED,
                ],
            ).exclude_directly_deleted()
            .values_list('task_id', flat=True),
        )

        if not user_task_ids:
            continue

        # Tasks where substitute group is already assigned
        already_delegated_task_ids = set(
            TaskPerformer.objects.filter(
                group=sub_group,
                type=PerformerType.GROUP,
                task_id__in=user_task_ids,
            ).values_list('task_id', flat=True),
        )

        tasks_to_delegate = user_task_ids - already_delegated_task_ids
        if not tasks_to_delegate:
            continue

        tasks = Task.objects.filter(
            id__in=tasks_to_delegate,
        ).select_related('workflow')

        performers_to_create = []
        wf_ids = set()
        for task in tasks:
            performers_to_create.append(
                TaskPerformer(
                    task=task,
                    type=PerformerType.GROUP,
                    group=sub_group,
                ),
            )
            wf_ids.add(task.workflow_id)
        if performers_to_create:
            TaskPerformer.objects.bulk_create(
                performers_to_create,
                ignore_conflicts=True,
            )
            for task in tasks:
                WorkflowEventService.task_delegation_event(
                    task=task,
                    user=user,
                    substitute_group=sub_group,
                )
            sub_ids = list(
                sub_group.users.values_list('id', flat=True),
            )
            if wf_ids and sub_ids:
                members_to_create = [
                    Workflow.members.through(
                        workflow_id=wf_id,
                        user_id=sub_id,
                    )
                    for wf_id in wf_ids
                    for sub_id in sub_ids
                ]
                Workflow.members.through.objects.bulk_create(
                    members_to_create,
                    ignore_conflicts=True,
                )
