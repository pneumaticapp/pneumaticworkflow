import logging
from typing import List
from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q

from src.accounts.enums import AbsenceStatus
from src.accounts.services.vacation import VacationDelegationService
from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    PerformerType,
    TaskStatus,
    WorkflowStatus,
)
from src.processes.models.workflows.task import Task, TaskPerformer
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
            workflow__status=WorkflowStatus.RUNNING,
        )
        .filter(
            Q(
                taskperformer__user_id=user_id,
                taskperformer__type=PerformerType.USER,
            )
            | Q(
                taskperformer__type=PerformerType.GROUP,
                taskperformer__group__users__id=user_id,
            ),
        )
        .select_related('workflow')
        .exclude_directly_deleted()
        .distinct()
    )
    for task in tasks:
        if not task.can_be_completed():
            continue
        service = WorkflowActionService(
            workflow=task.workflow,
            user=user,
            is_superuser=is_superuser,
            auth_type=auth_type,
        )
        service.complete_task(task)


@shared_task
def check_and_complete_tasks(
    task_ids: List[int],
    is_superuser: bool,
    auth_type: AuthTokenType.LITERALS,
    account_id: int,
):

    user = UserModel.objects.get(account_id=account_id, is_account_owner=True)
    tasks = (
        Task.objects
        .filter(id__in=task_ids)
        .select_related('workflow')
        .order_by('id')
    )
    for task in tasks:
        if task.can_be_completed():
            service = WorkflowActionService(
                is_superuser=is_superuser,
                auth_type=auth_type,
                user=user,
                workflow=task.workflow,
            )
            service.complete_task(task)


@shared_task
def delegate_vacation_tasks():
    """Find active tasks belonging to vacationing users and
    add their substitute group as performer asynchronously.
    """
    vacationing_users = UserModel.objects.filter(
        vacations__isnull=False,
        vacations__is_deleted=False,
        vacations__absence_status__in=[
            AbsenceStatus.VACATION,
            AbsenceStatus.SICK_LEAVE,
        ],
        vacations__substitute_group__isnull=False,
    ).order_by('id')

    logger = logging.getLogger(__name__)

    for user in vacationing_users:
        try:
            with transaction.atomic():
                _delegate_tasks_for_user(user)
        except Exception:
            logger.exception(
                'Failed to delegate vacation tasks for user %d',
                user.id,
            )
            continue


def _delegate_tasks_for_user(user):
    vacation = user.vacation
    if not vacation:
        return
    sub_group = vacation.substitute_group

    # Already-delegated tasks (including soft-deleted)
    already_delegated_task_ids = set(
        TaskPerformer.objects.filter(
            group=sub_group,
            type=PerformerType.GROUP,
        ).values_list('task_id', flat=True),
    )

    service = VacationDelegationService(user)
    _, wf_ids = service.delegate_tasks(
        group=sub_group,
        existing_task_ids=already_delegated_task_ids,
    )

    if not wf_ids:
        return

    sub_ids = list(
        sub_group.users.values_list('id', flat=True),
    )
    VacationDelegationService.add_members_bulk(
        wf_ids=wf_ids,
        substitute_user_ids=sub_ids,
    )
