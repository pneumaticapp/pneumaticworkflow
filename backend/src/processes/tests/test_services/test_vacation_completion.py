from datetime import datetime, timezone

import pytest

from src.accounts.enums import AbsenceStatus, UserGroupType
from src.accounts.models import UserVacation
from src.processes.enums import PerformerType, TaskStatus
from src.processes.models.workflows.task import TaskPerformer
from src.processes.services.workflow_action import WorkflowActionService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_owner,
    create_test_workflow,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def delegated_task(mocker):
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(account=account, email='sub@test.test')
    absent = create_test_admin(account=account, email='absent@test.test')
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])
    group = create_test_group(
        account=account,
        users=[substitute],
        type_=UserGroupType.PERSONAL,
    )
    vacation = UserVacation.objects.create(
        user=absent,
        account=account,
        substitute_group=group,
        absence_status=AbsenceStatus.VACATION,
    )
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    )
    absent_performer = TaskPerformer.objects.create(
        task=task,
        user=absent,
        type=PerformerType.USER,
    )
    completed_at = datetime(2026, 10, 6, tzinfo=timezone.utc)
    mocker.patch(
        'src.processes.services.workflow_action.timezone.now',
        return_value=completed_at,
    )
    return task, substitute, vacation, absent_performer, completed_at


@pytest.mark.parametrize(
    'absence_status',
    (AbsenceStatus.VACATION, AbsenceStatus.SICK_LEAVE),
)
def test_complete_substitute__absent_share_completed(
    delegated_task,
    absence_status,
):
    # arrange
    task, substitute, vacation, absent_performer, completed_at = delegated_task
    vacation.absence_status = absence_status
    vacation.save(update_fields=['absence_status'])
    service = WorkflowActionService(user=substitute, workflow=task.workflow)

    # act
    service._complete_performers_for_user(task=task)

    # assert
    absent_performer.refresh_from_db()
    assert absent_performer.is_completed is True
    assert absent_performer.date_completed == completed_at
    assert TaskPerformer.objects.get(
        task=task,
        user=substitute,
        type=PerformerType.GROUP_USER,
    ).is_completed is True
    assert task.taskperformer_set.get(
        user=task.workflow.workflow_starter,
    ).is_completed is False
    assert task.can_be_completed() is False


@pytest.mark.parametrize(
    'absence_status, vacation_deleted, group_type, group_deleted',
    (
        (AbsenceStatus.ACTIVE, False, UserGroupType.PERSONAL, False),
        (AbsenceStatus.VACATION, True, UserGroupType.PERSONAL, False),
        (AbsenceStatus.VACATION, False, UserGroupType.REGULAR, False),
        (AbsenceStatus.VACATION, False, UserGroupType.PERSONAL, True),
    ),
)
def test_complete_substitute__ineligible_absence__share_unchanged(
    delegated_task,
    absence_status,
    vacation_deleted,
    group_type,
    group_deleted,
):
    # arrange
    task, substitute, vacation, absent_performer, _ = delegated_task
    vacation.absence_status = absence_status
    vacation.is_deleted = vacation_deleted
    vacation.save(update_fields=['absence_status', 'is_deleted'])
    group = vacation.substitute_group
    group.type = group_type
    group.is_deleted = group_deleted
    group.save(update_fields=['type', 'is_deleted'])
    service = WorkflowActionService(user=substitute, workflow=task.workflow)

    # act
    service._complete_performers_for_user(task=task)

    # assert
    absent_performer.refresh_from_db()
    assert absent_performer.is_completed is False
    assert absent_performer.date_completed is None


def test_complete_substitute__absent_group_member__share_completed(
    delegated_task,
):
    # arrange
    task, substitute, vacation, absent_performer, completed_at = delegated_task
    absent_performer.delete()
    regular_group = create_test_group(
        account=task.account,
        name='Regular performers',
        users=[vacation.user, task.workflow.workflow_starter],
    )
    TaskPerformer.objects.create(
        task=task,
        group=regular_group,
        type=PerformerType.GROUP,
    )
    service = WorkflowActionService(user=substitute, workflow=task.workflow)

    # act
    service._complete_performers_for_user(task=task)

    # assert
    absent_marker = TaskPerformer.objects.get(
        task=task,
        user=vacation.user,
        type=PerformerType.GROUP_USER,
    )
    assert absent_marker.is_completed is True
    assert absent_marker.date_completed == completed_at
    assert task.can_be_completed() is False


def test_complete_substitute__without_rcba__absent_share_completed(
    delegated_task,
):
    # arrange
    task, substitute, _, absent_performer, completed_at = delegated_task
    task.require_completion_by_all = False
    task.save(update_fields=['require_completion_by_all'])
    service = WorkflowActionService(user=substitute, workflow=task.workflow)

    # act
    service._complete_performers_for_user(task=task)

    # assert
    absent_performer.refresh_from_db()
    assert absent_performer.is_completed is True
    assert absent_performer.date_completed == completed_at
    assert task.taskperformer_set.get(type=PerformerType.GROUP).is_completed


def test_complete_substitute__shared_group__all_absent_shares_completed(
    delegated_task,
):
    # arrange
    task, substitute, vacation, absent_performer, completed_at = delegated_task
    second_absent = create_test_admin(
        account=task.account,
        email='second-absent@test.test',
    )
    UserVacation.objects.create(
        user=second_absent,
        account=task.account,
        substitute_group=vacation.substitute_group,
        absence_status=AbsenceStatus.SICK_LEAVE,
    )
    second_performer = TaskPerformer.objects.create(
        task=task,
        user=second_absent,
        type=PerformerType.USER,
    )
    service = WorkflowActionService(user=substitute, workflow=task.workflow)

    # act
    service._complete_performers_for_user(task=task)

    # assert
    absent_performer.refresh_from_db()
    second_performer.refresh_from_db()
    assert absent_performer.is_completed is True
    assert second_performer.is_completed is True
    assert second_performer.date_completed == completed_at


def test_complete_substitute__circular_delegation__terminates(delegated_task):
    # arrange
    task, substitute, vacation, absent_performer, _ = delegated_task
    reverse_group = create_test_group(
        account=task.account,
        name='Reverse substitution',
        users=[vacation.user],
        type_=UserGroupType.PERSONAL,
    )
    UserVacation.objects.create(
        user=substitute,
        account=task.account,
        substitute_group=reverse_group,
        absence_status=AbsenceStatus.SICK_LEAVE,
    )
    TaskPerformer.objects.create(
        task=task,
        group=reverse_group,
        type=PerformerType.GROUP,
    )
    service = WorkflowActionService(user=substitute, workflow=task.workflow)

    # act
    service._complete_performers_for_user(task=task)
    service._complete_performers_for_user(task=task)

    # assert
    absent_performer.refresh_from_db()
    assert absent_performer.is_completed is True
    assert task.taskperformer_set.filter(
        type=PerformerType.GROUP_USER,
        is_completed=True,
    ).count() == 2


def test_complete_substitute__last_shares__task_completed(
    delegated_task,
    mocker,
):
    # arrange
    task, substitute, _, absent_performer, _ = delegated_task
    owner_performer = task.taskperformer_set.get(
        user=task.workflow.workflow_starter,
    )
    owner_performer.is_completed = True
    owner_performer.save(update_fields=['is_completed'])
    mocker.patch(
        'src.processes.services.workflow_action.'
        'send_task_completed_websocket.delay',
    )
    mocker.patch(
        'src.processes.services.workflow_action.'
        'send_task_completed_notification.delay',
    )
    mocker.patch.object(WorkflowActionService, '_start_next_tasks')
    service = WorkflowActionService(user=substitute, workflow=task.workflow)

    # act
    service.complete_task_for_user(task=task)

    # assert
    task.refresh_from_db()
    absent_performer.refresh_from_db()
    assert task.status == TaskStatus.COMPLETED
    assert absent_performer.is_completed is True


def test_complete_substitute__independent_share__task_stays_active(
    delegated_task,
    mocker,
):
    # arrange
    task, substitute, _, absent_performer, _ = delegated_task
    mocker.patch(
        'src.processes.services.workflow_action.'
        'send_task_completed_websocket.delay',
    )
    service = WorkflowActionService(user=substitute, workflow=task.workflow)

    # act
    service.complete_task_for_user(task=task)

    # assert
    task.refresh_from_db()
    absent_performer.refresh_from_db()
    assert task.status == TaskStatus.ACTIVE
    assert absent_performer.is_completed is True
    assert task.taskperformer_set.get(
        user=task.workflow.workflow_starter,
    ).is_completed is False
