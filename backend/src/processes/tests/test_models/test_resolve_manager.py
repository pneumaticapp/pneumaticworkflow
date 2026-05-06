import pytest
from unittest.mock import Mock
from django.utils import timezone

from src.processes.enums import TaskStatus
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_user,
    create_test_workflow,
)


pytestmark = pytest.mark.django_db


def test_resolve_manager__ok():

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

    tp = source_task.taskperformer_set.first()
    tp.user = subordinate
    tp.date_completed = timezone.now()
    tp.save()

    target_task = workflow.tasks.get(number=2)

    raw_perf = Mock(source_task_api_name=source_task.api_name)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result == manager


def test_resolve_manager__source_not_completed__none():

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner)
    source_task = workflow.tasks.get(number=1)

    # keep source active (not completed)
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

    tp = source_task.taskperformer_set.first()
    tp.user = subordinate
    tp.date_completed = timezone.now()
    tp.save()

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

    tp = source_task.taskperformer_set.first()
    tp.user = None
    tp.date_completed = timezone.now()
    tp.save()

    target_task = workflow.tasks.get(number=2)

    raw_perf = Mock(source_task_api_name=source_task.api_name)

    # act
    result = target_task._resolve_manager(raw_perf)

    # assert
    assert result is None
