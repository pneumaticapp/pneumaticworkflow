import pytest
from django.contrib.auth import get_user_model

from src.authentication.enums import AuthTokenType
from src.processes.enums import TaskStatus
from src.processes.models.workflows.task import Task
from src.processes.services.workflow_action import WorkflowActionService
from src.processes.tasks.tasks import check_and_complete_tasks
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_workflow,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_check_and_complete_tasks__empty_task_ids__skip(mocker):

    """
    Empty task_ids — does not initialize WorkflowActionService
    or call complete_task
    """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    task_ids = []
    is_superuser = False
    auth_type = AuthTokenType.USER
    can_be_completed_mock = mocker.patch.object(
        Task,
        attribute='can_be_completed',
        return_value=True,
    )
    workflow_action_service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_mock = mocker.patch(
        target='src.processes.tasks.tasks.WorkflowActionService.complete_task',
    )

    # act
    check_and_complete_tasks(
        task_ids=task_ids,
        is_superuser=is_superuser,
        auth_type=auth_type,
        account_id=account.id,
    )

    # assert
    can_be_completed_mock.assert_not_called()
    workflow_action_service_init_mock.assert_not_called()
    complete_task_mock.assert_not_called()


def test_check_and_complete_tasks__unknown_task_ids__skip(mocker):

    """
    Unknown task ids — does not initialize WorkflowActionService or
    call complete_task
    """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    task_ids = [-1]
    is_superuser = False
    auth_type = AuthTokenType.USER
    can_be_completed_mock = mocker.patch.object(
        Task,
        attribute='can_be_completed',
        return_value=True,
    )
    workflow_action_service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_mock = mocker.patch(
        target='src.processes.tasks.tasks.WorkflowActionService.complete_task',
    )

    # act
    check_and_complete_tasks(
        task_ids=task_ids,
        is_superuser=is_superuser,
        auth_type=auth_type,
        account_id=account.id,
    )

    # assert
    can_be_completed_mock.assert_not_called()
    workflow_action_service_init_mock.assert_not_called()
    complete_task_mock.assert_not_called()


def test_check_and_complete_tasks__ok(mocker):

    """
    Completable task — initializes WorkflowActionService with account owner
    and calls complete_task
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow_1 = create_test_workflow(user=owner, tasks_count=1)
    task_1 = workflow_1.tasks.get(number=1)
    task_ids = [task_1.id]
    is_superuser = False
    auth_type = AuthTokenType.USER
    can_be_completed_mock = mocker.patch.object(
        Task,
        attribute='can_be_completed',
        return_value=True,
    )
    workflow_action_service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_mock = mocker.patch(
        target='src.processes.tasks.tasks.WorkflowActionService.complete_task',
    )

    # act
    check_and_complete_tasks(
        task_ids=task_ids,
        is_superuser=is_superuser,
        auth_type=auth_type,
        account_id=account.id,
    )

    # assert
    can_be_completed_mock.assert_called_once_with()
    workflow_action_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        user=owner,
        workflow=task_1.workflow,
    )
    complete_task_mock.assert_called_once_with(task_1)


def test_check_and_complete_tasks__not_completable_task__skip(mocker):

    """
    Task cannot be completed — does not initialize WorkflowActionService
    or call complete_task
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow_1 = create_test_workflow(user=owner, tasks_count=1)
    task_1 = workflow_1.tasks.get(number=1)
    task_ids = [task_1.id]
    is_superuser = False
    auth_type = AuthTokenType.USER
    can_be_completed_mock = mocker.patch.object(
        Task,
        attribute='can_be_completed',
        return_value=False,
    )
    workflow_action_service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_mock = mocker.patch(
        target='src.processes.tasks.tasks.WorkflowActionService.complete_task',
    )

    # act
    check_and_complete_tasks(
        task_ids=task_ids,
        is_superuser=is_superuser,
        auth_type=auth_type,
        account_id=account.id,
    )

    # assert
    can_be_completed_mock.assert_called_once_with()
    workflow_action_service_init_mock.assert_not_called()
    complete_task_mock.assert_not_called()


@pytest.mark.parametrize('status', TaskStatus.INACTIVE_STATUS)
def test_check_and_complete_tasks__not_active_task__skip(status, mocker):

    """
    Task is no longer active (e.g. became PENDING/DELAYED after enqueue) —
    does not complete it even if can_be_completed would return True.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow_1 = create_test_workflow(user=owner, tasks_count=1)
    task_1 = workflow_1.tasks.get(number=1)
    task_1.status = status
    task_1.save(update_fields=['status'])
    task_ids = [task_1.id]
    is_superuser = False
    auth_type = AuthTokenType.USER
    can_be_completed_mock = mocker.patch.object(
        Task,
        attribute='can_be_completed',
        return_value=True,
    )
    workflow_action_service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_mock = mocker.patch(
        target='src.processes.tasks.tasks.WorkflowActionService.complete_task',
    )

    # act
    check_and_complete_tasks(
        task_ids=task_ids,
        is_superuser=is_superuser,
        auth_type=auth_type,
        account_id=account.id,
    )

    # assert
    can_be_completed_mock.assert_not_called()
    workflow_action_service_init_mock.assert_not_called()
    complete_task_mock.assert_not_called()


def test_check_and_complete_tasks__multiple_tasks__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow_1 = create_test_workflow(user=owner, tasks_count=1)
    task_1 = workflow_1.tasks.get(number=1)
    workflow_2 = create_test_workflow(user=owner, tasks_count=1)
    task_2 = workflow_2.tasks.get(number=1)
    task_ids = [task_1.id, task_2.id]
    is_superuser = False
    auth_type = AuthTokenType.USER
    can_be_completed_mock = mocker.patch.object(
        Task,
        attribute='can_be_completed',
        return_value=True,
    )
    workflow_action_service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None,
    )
    complete_task_mock = mocker.patch(
        target='src.processes.tasks.tasks.WorkflowActionService.complete_task',
    )

    # act
    check_and_complete_tasks(
        task_ids=task_ids,
        is_superuser=is_superuser,
        auth_type=auth_type,
        account_id=account.id,
    )

    # assert
    assert can_be_completed_mock.call_count == 2
    can_be_completed_mock.assert_has_calls(
        calls=[
            mocker.call(),
            mocker.call(),
        ],
        any_order=True,
    )
    assert workflow_action_service_init_mock.call_count == 2
    workflow_action_service_init_mock.assert_has_calls(
        calls=[
            mocker.call(
                is_superuser=False,
                auth_type=AuthTokenType.USER,
                user=owner,
                workflow=task_1.workflow,
            ),
            mocker.call(
                is_superuser=False,
                auth_type=AuthTokenType.USER,
                user=owner,
                workflow=task_2.workflow,
            ),
        ],
        any_order=True,
    )
    assert complete_task_mock.call_count == 2
    complete_task_mock.assert_has_calls(
        calls=[
            mocker.call(task_1),
            mocker.call(task_2),
        ],
        any_order=True,
    )
