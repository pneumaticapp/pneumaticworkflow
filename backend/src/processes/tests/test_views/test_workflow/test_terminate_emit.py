import pytest

from src.authentication.enums import AuthTokenType
from src.processes.models.workflows.workflow import Workflow
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_destroy__account_owner__audit_workflow_terminated(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
    )
    task = workflow.tasks.get(number=1)
    task_data = task.get_data_for_list()
    send_task_deleted_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'send_task_deleted_notification.delay',
    )
    deactivate_guest_mock = mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.deactivate_task_guest_cache',
    )
    workflows_terminated_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.workflows_terminated',
    )
    workflow_terminated_mock = mocker.patch(
        'src.processes.services.workflow_action.AuditEventService'
        '.workflow_terminated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.delete(path=f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 204
    assert not Workflow.objects.filter(id=workflow.id).exists()
    send_task_deleted_mock.assert_called_once_with(
        task_id=task.id,
        task_data=task_data,
        recipients=[(owner.id, owner.email)],
        account_id=account.id,
    )
    deactivate_guest_mock.assert_called_once_with(task_id=task.id)
    workflows_terminated_mock.assert_called_once_with(
        user=owner,
        workflow=workflow,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    workflow_terminated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
    )


def test_destroy__workflow_of_another_account__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    another_account = create_test_account(name='Another')
    another_owner = create_test_owner(
        account=another_account,
        email='another@test.test',
    )
    workflow = create_test_workflow(
        user=another_owner,
        tasks_count=1,
    )
    send_task_deleted_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'send_task_deleted_notification.delay',
    )
    deactivate_guest_mock = mocker.patch(
        'src.processes.services.workflow_action.GuestJWTAuthService'
        '.deactivate_task_guest_cache',
    )
    workflows_terminated_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.workflows_terminated',
    )
    workflow_terminated_mock = mocker.patch(
        'src.processes.services.workflow_action.AuditEventService'
        '.workflow_terminated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.delete(path=f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 404
    assert Workflow.objects.filter(id=workflow.id).exists()
    send_task_deleted_mock.assert_not_called()
    deactivate_guest_mock.assert_not_called()
    workflows_terminated_mock.assert_not_called()
    workflow_terminated_mock.assert_not_called()
