import pytest
from unittest.mock import Mock
from django.utils import timezone

from src.accounts.enums import UserStatus
from src.processes.enums import (
    PerformerType,
    TaskStatus,
    WorkflowEventType,
)
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_event,
    create_test_group,
    create_test_owner,
    create_test_user,
    create_test_workflow,
)


pytestmark = pytest.mark.django_db


def test_resolve_manager__single_user__ok():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    subordinate = create_test_user(
        email='sub@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    manager = create_test_user(
        email='mgr@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    subordinate.manager = manager
    subordinate.save()

    workflow = create_test_workflow(user=owner)
    source_task = workflow.tasks.get(number=1)
    source_task.status = TaskStatus.COMPLETED
    source_task.date_completed = timezone.now()
    source_task.save()

    create_test_event(
        workflow=workflow,
        user=subordinate,
        type_event=WorkflowEventType.TASK_COMPLETE,
        task=source_task,
    )

    target_task = workflow.tasks.get(number=2)
    raw_perf = Mock(source_task_api_name=source_task.api_name)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result == manager


def test_resolve_manager__two_users__returns_completer_manager():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_a = create_test_user(
        email='a@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    user_b = create_test_user(
        email='b@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    manager_a = create_test_user(
        email='mgr_a@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    user_a.manager = manager_a
    user_a.save()

    workflow = create_test_workflow(user=owner)
    source_task = workflow.tasks.get(number=1)
    source_task.status = TaskStatus.COMPLETED
    source_task.date_completed = timezone.now()
    source_task.save()

    # Both performers get date_completed (bulk update)
    source_task.add_raw_performer(
        user=user_a,
        performer_type=PerformerType.USER,
    )
    source_task.add_raw_performer(
        user=user_b,
        performer_type=PerformerType.USER,
    )
    source_task.taskperformer_set.update(
        is_completed=True,
        date_completed=timezone.now(),
    )

    # Event records user_a as actual completer
    create_test_event(
        workflow=workflow,
        user=user_a,
        type_event=WorkflowEventType.TASK_COMPLETE,
        task=source_task,
    )

    target_task = workflow.tasks.get(number=2)
    raw_perf = Mock(source_task_api_name=source_task.api_name)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result == manager_a


def test_resolve_manager__single_group__returns_completer_manager():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_a = create_test_user(
        email='a@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    manager_a = create_test_user(
        email='mgr_a@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    user_a.manager = manager_a
    user_a.save()

    group = create_test_group(
        account=account,
        name='Group1',
        users=[user_a],
    )

    workflow = create_test_workflow(user=owner)
    source_task = workflow.tasks.get(number=1)
    source_task.status = TaskStatus.COMPLETED
    source_task.date_completed = timezone.now()
    source_task.save()

    source_task.add_raw_performer(
        group_id=group.id,
        performer_type=PerformerType.GROUP,
    )
    source_task.taskperformer_set.update(
        is_completed=True,
        date_completed=timezone.now(),
    )

    # user_a from the group completed the task
    create_test_event(
        workflow=workflow,
        user=user_a,
        type_event=WorkflowEventType.TASK_COMPLETE,
        task=source_task,
    )

    target_task = workflow.tasks.get(number=2)
    raw_perf = Mock(source_task_api_name=source_task.api_name)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result == manager_a


def test_resolve_manager__group_and_user__group_member_completes():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_a = create_test_user(
        email='a@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    user_b = create_test_user(
        email='b@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    manager_a = create_test_user(
        email='mgr_a@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    user_a.manager = manager_a
    user_a.save()

    group = create_test_group(
        account=account,
        name='Group1',
        users=[user_a],
    )

    workflow = create_test_workflow(user=owner)
    source_task = workflow.tasks.get(number=1)
    source_task.status = TaskStatus.COMPLETED
    source_task.date_completed = timezone.now()
    source_task.save()

    source_task.add_raw_performer(
        group_id=group.id,
        performer_type=PerformerType.GROUP,
    )
    source_task.add_raw_performer(
        user=user_b,
        performer_type=PerformerType.USER,
    )
    source_task.taskperformer_set.update(
        is_completed=True,
        date_completed=timezone.now(),
    )

    # user_a from group completed
    create_test_event(
        workflow=workflow,
        user=user_a,
        type_event=WorkflowEventType.TASK_COMPLETE,
        task=source_task,
    )

    target_task = workflow.tasks.get(number=2)
    raw_perf = Mock(source_task_api_name=source_task.api_name)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result == manager_a


def test_resolve_manager__two_groups__returns_completer_manager():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_a = create_test_user(
        email='a@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    manager_a = create_test_user(
        email='mgr_a@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    user_a.manager = manager_a
    user_a.save()

    user_c = create_test_user(
        email='c@pneumatic.app',
        account=account,
        is_account_owner=False,
    )

    group1 = create_test_group(
        account=account,
        name='Group1',
        users=[user_a],
    )
    group2 = create_test_group(
        account=account,
        name='Group2',
        users=[user_c],
    )

    workflow = create_test_workflow(user=owner)
    source_task = workflow.tasks.get(number=1)
    source_task.status = TaskStatus.COMPLETED
    source_task.date_completed = timezone.now()
    source_task.save()

    source_task.add_raw_performer(
        group_id=group1.id,
        performer_type=PerformerType.GROUP,
    )
    source_task.add_raw_performer(
        group_id=group2.id,
        performer_type=PerformerType.GROUP,
    )
    source_task.taskperformer_set.update(
        is_completed=True,
        date_completed=timezone.now(),
    )

    create_test_event(
        workflow=workflow,
        user=user_a,
        type_event=WorkflowEventType.TASK_COMPLETE,
        task=source_task,
    )

    target_task = workflow.tasks.get(number=2)
    raw_perf = Mock(source_task_api_name=source_task.api_name)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result == manager_a


def test_resolve_manager__two_groups_two_users__returns_completer_manager():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_a = create_test_user(
        email='a@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    user_b = create_test_user(
        email='b@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    manager_a = create_test_user(
        email='mgr_a@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    user_a.manager = manager_a
    user_a.save()

    user_c = create_test_user(
        email='c@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    user_d = create_test_user(
        email='d@pneumatic.app',
        account=account,
        is_account_owner=False,
    )

    group1 = create_test_group(
        account=account,
        name='Group1',
        users=[user_c],
    )
    group2 = create_test_group(
        account=account,
        name='Group2',
        users=[user_d],
    )

    workflow = create_test_workflow(user=owner)
    source_task = workflow.tasks.get(number=1)
    source_task.status = TaskStatus.COMPLETED
    source_task.date_completed = timezone.now()
    source_task.save()

    source_task.add_raw_performer(
        group_id=group1.id,
        performer_type=PerformerType.GROUP,
    )
    source_task.add_raw_performer(
        group_id=group2.id,
        performer_type=PerformerType.GROUP,
    )
    source_task.add_raw_performer(
        user=user_a,
        performer_type=PerformerType.USER,
    )
    source_task.add_raw_performer(
        user=user_b,
        performer_type=PerformerType.USER,
    )
    source_task.taskperformer_set.update(
        is_completed=True,
        date_completed=timezone.now(),
    )

    create_test_event(
        workflow=workflow,
        user=user_a,
        type_event=WorkflowEventType.TASK_COMPLETE,
        task=source_task,
    )

    target_task = workflow.tasks.get(number=2)
    raw_perf = Mock(source_task_api_name=source_task.api_name)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result == manager_a


def test_resolve_manager__user_in_own_group__returns_manager():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_a = create_test_user(
        email='a@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    manager_a = create_test_user(
        email='mgr_a@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    user_a.manager = manager_a
    user_a.save()

    group = create_test_group(
        account=account,
        name='Group1',
        users=[user_a],
    )

    workflow = create_test_workflow(user=owner)
    source_task = workflow.tasks.get(number=1)
    source_task.status = TaskStatus.COMPLETED
    source_task.date_completed = timezone.now()
    source_task.save()

    source_task.add_raw_performer(
        user=user_a,
        performer_type=PerformerType.USER,
    )
    source_task.add_raw_performer(
        group_id=group.id,
        performer_type=PerformerType.GROUP,
    )
    source_task.taskperformer_set.update(
        is_completed=True,
        date_completed=timezone.now(),
    )

    create_test_event(
        workflow=workflow,
        user=user_a,
        type_event=WorkflowEventType.TASK_COMPLETE,
        task=source_task,
    )

    target_task = workflow.tasks.get(number=2)
    raw_perf = Mock(source_task_api_name=source_task.api_name)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result == manager_a


def test_resolve_manager__empty_group__no_event__none():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)

    create_test_group(
        account=account,
        name='EmptyGroup',
        users=[],
    )

    workflow = create_test_workflow(user=owner)
    source_task = workflow.tasks.get(number=1)
    # Task cannot be completed by anyone вЂ” no TASK_COMPLETE event

    target_task = workflow.tasks.get(number=2)
    raw_perf = Mock(source_task_api_name=source_task.api_name)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result is None


def test_resolve_manager__source_not_completed__none():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    source_task = workflow.tasks.get(number=1)

    # keep source active (not completed) вЂ” no TASK_COMPLETE event
    source_task.status = TaskStatus.ACTIVE
    source_task.save()

    target_task = workflow.tasks.get(number=2)
    raw_perf = Mock(source_task_api_name=source_task.api_name)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result is None


def test_resolve_manager__no_manager__none():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    subordinate = create_test_user(
        email='sub@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    # no manager set

    workflow = create_test_workflow(user=owner)
    source_task = workflow.tasks.get(number=1)
    source_task.status = TaskStatus.COMPLETED
    source_task.date_completed = timezone.now()
    source_task.save()

    create_test_event(
        workflow=workflow,
        user=subordinate,
        type_event=WorkflowEventType.TASK_COMPLETE,
        task=source_task,
    )

    target_task = workflow.tasks.get(number=2)
    raw_perf = Mock(source_task_api_name=source_task.api_name)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result is None


def test_resolve_manager__empty_api_name__none():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    target_task = workflow.tasks.get(number=2)

    raw_perf = Mock(source_task_api_name=None)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result is None


def test_resolve_manager__nonexistent_api_name__none():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    target_task = workflow.tasks.get(number=2)

    raw_perf = Mock(source_task_api_name='nonexistent-task')

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result is None


def test_resolve_manager__completer_user_deleted__none():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)

    workflow = create_test_workflow(user=owner)
    source_task = workflow.tasks.get(number=1)
    source_task.status = TaskStatus.COMPLETED
    source_task.date_completed = timezone.now()
    source_task.save()

    create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.TASK_COMPLETE,
        task=source_task,
    )
    WorkflowEvent.objects.filter(
        workflow=workflow,
        type=WorkflowEventType.TASK_COMPLETE,
    ).update(user=None)

    target_task = workflow.tasks.get(number=2)
    raw_perf = Mock(source_task_api_name=source_task.api_name)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result is None


def test_resolve_manager__owner_force_completes__none():
    """
    Account owner force-completes the source task (not a performer).
    Owner has no manager — returns None.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)

    workflow = create_test_workflow(user=owner)
    source_task = workflow.tasks.get(number=1)
    source_task.status = TaskStatus.COMPLETED
    source_task.date_completed = timezone.now()
    source_task.save()

    create_test_event(
        workflow=workflow,
        user=owner,
        type_event=WorkflowEventType.TASK_COMPLETE,
        task=source_task,
    )

    target_task = workflow.tasks.get(number=2)
    raw_perf = Mock(source_task_api_name=source_task.api_name)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result is None


def test_resolve_manager__inactive_manager__none():
    """
    Manager exists but has been deactivated (status=INACTIVE).
    Should return None — inactive managers must not be assigned.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    subordinate = create_test_user(
        email='sub@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    manager = create_test_user(
        email='mgr@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    subordinate.manager = manager
    subordinate.save()
    manager.status = UserStatus.INACTIVE
    manager.save(update_fields=['status'])

    workflow = create_test_workflow(user=owner)
    source_task = workflow.tasks.get(number=1)
    source_task.status = TaskStatus.COMPLETED
    source_task.date_completed = timezone.now()
    source_task.save()

    create_test_event(
        workflow=workflow,
        user=subordinate,
        type_event=WorkflowEventType.TASK_COMPLETE,
        task=source_task,
    )

    target_task = workflow.tasks.get(number=2)
    raw_perf = Mock(source_task_api_name=source_task.api_name)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result is None


def test_resolve_manager__invited_manager__none():
    """
    Manager exists but has status=INVITED (not yet active).
    Should return None — only active managers are valid.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    subordinate = create_test_user(
        email='sub@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    manager = create_test_user(
        email='mgr@pneumatic.app',
        account=account,
        is_account_owner=False,
    )
    subordinate.manager = manager
    subordinate.save()

    manager.status = UserStatus.INVITED
    manager.save(update_fields=['status'])

    workflow = create_test_workflow(user=owner)
    source_task = workflow.tasks.get(number=1)
    source_task.status = TaskStatus.COMPLETED
    source_task.date_completed = timezone.now()
    source_task.save()

    create_test_event(
        workflow=workflow,
        user=subordinate,
        type_event=WorkflowEventType.TASK_COMPLETE,
        task=source_task,
    )

    target_task = workflow.tasks.get(number=2)
    raw_perf = Mock(source_task_api_name=source_task.api_name)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result is None
