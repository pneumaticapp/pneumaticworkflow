import pytest

from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.models.workflows.workflow import Workflow
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_destroy__account_owner__emit_workflow_terminate(
    mocker,
    api_client,
    fake_stream,
):

    """ The workflow is gone by the end of the request: the name and
        the template of the deleted process have to be in the event
        itself. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        name='Onboarding of Ann Smith',
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
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.26',
    )

    # act
    response = api_client.delete(
        path=f'/workflows/{workflow.id}',
        HTTP_X_REQUEST_ID='audit-workflow-26',
    )

    # assert
    assert response.status_code == 204
    assert not Workflow.objects.filter(id=workflow.id).exists()
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.WORKFLOW_TERMINATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.WORKFLOW,
        id=workflow.id,
    )
    assert event.workflow_id == workflow.id
    assert event.task_id is None
    assert event.payload == {
        'workflow_name': 'Onboarding of Ann Smith',
        'template_id': workflow.template_id,
    }
    assert event.ip == '10.10.0.26'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-workflow-26'
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


def test_destroy__workflow_of_another_account__not_found(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    another_account = create_test_account(name='Another')
    another_owner = create_test_owner(
        account=another_account,
        email='another@test.test',
    )
    workflow = create_test_workflow(user=another_owner, tasks_count=1)
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
    api_client.token_authenticate(owner)

    # act
    response = api_client.delete(path=f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 404
    assert Workflow.objects.filter(id=workflow.id).exists()
    assert fake_stream.events == []
    send_task_deleted_mock.assert_not_called()
    deactivate_guest_mock.assert_not_called()
    workflows_terminated_mock.assert_not_called()
