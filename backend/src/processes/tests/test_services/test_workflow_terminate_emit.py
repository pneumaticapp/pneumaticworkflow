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
from src.processes.services.workflow_action import WorkflowActionService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_terminate_workflow__user_action__emit_workflow_terminate(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
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
    analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.workflows_terminated',
    )
    emit_mock = mocker.patch(
        'src.logs.events.mixins.emit',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.terminate_workflow()

    # assert
    assert not Workflow.objects.filter(id=workflow.id).exists()
    emit_mock.assert_called_once_with(
        EventName.WORKFLOW_TERMINATE,
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(
            type=EventObjectType.WORKFLOW,
            id=workflow.id,
        ),
        workflow_id=workflow.id,
        payload={
            'workflow_name': workflow.name,
            'template_id': workflow.template_id,
        },
    )
    send_task_deleted_mock.assert_called_once_with(
        task_id=task.id,
        task_data=task_data,
        recipients=[(owner.id, owner.email)],
        account_id=account.id,
    )
    deactivate_guest_mock.assert_called_once_with(task_id=task.id)
    analytics_mock.assert_called_once_with(
        user=owner,
        workflow=workflow,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_terminate_workflow__api_key_auth__emit_api_key_actor_type(
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
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
    analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.workflows_terminated',
    )
    emit_mock = mocker.patch(
        'src.logs.events.mixins.emit',
    )
    service = WorkflowActionService(
        user=owner,
        workflow=workflow,
        auth_type=AuthTokenType.API,
    )

    # act
    service.terminate_workflow()

    # assert
    emit_mock.assert_called_once_with(
        EventName.WORKFLOW_TERMINATE,
        account_id=account.id,
        actor=Actor(
            type=ActorType.API_KEY,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(
            type=EventObjectType.WORKFLOW,
            id=workflow.id,
        ),
        workflow_id=workflow.id,
        payload={
            'workflow_name': workflow.name,
            'template_id': workflow.template_id,
        },
    )
    send_task_deleted_mock.assert_called_once_with(
        task_id=task.id,
        task_data=task_data,
        recipients=[(owner.id, owner.email)],
        account_id=account.id,
    )
    deactivate_guest_mock.assert_called_once_with(task_id=task.id)
    analytics_mock.assert_called_once_with(
        user=owner,
        workflow=workflow,
        is_superuser=False,
        auth_type=AuthTokenType.API,
    )


def test_terminate_workflow__deleted_workflow__event_keeps_the_name(
    mocker,
    fake_stream,
):

    """ The workflow is gone by the end of the method, so the name
        and the template of the deleted process have to be in the
        event itself. """

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
    analytics_mock = mocker.patch(
        'src.processes.services.workflow_action.AnalyticService'
        '.workflows_terminated',
    )
    service = WorkflowActionService(user=owner, workflow=workflow)

    # act
    service.terminate_workflow()

    # assert
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
    assert event.payload == {
        'workflow_name': 'Onboarding of Ann Smith',
        'template_id': workflow.template_id,
    }
    assert event.pii == ('actor.email', 'payload.workflow_name')
    send_task_deleted_mock.assert_called_once_with(
        task_id=task.id,
        task_data=task_data,
        recipients=[(owner.id, owner.email)],
        account_id=account.id,
    )
    deactivate_guest_mock.assert_called_once_with(task_id=task.id)
    analytics_mock.assert_called_once_with(
        user=owner,
        workflow=workflow,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
