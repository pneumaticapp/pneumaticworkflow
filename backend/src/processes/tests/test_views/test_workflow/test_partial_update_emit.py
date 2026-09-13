from datetime import timedelta

import pytest
from django.utils import timezone

from src.analysis.actions import WorkflowActions
from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.enums import WorkflowEventType
from src.processes.messages import workflow as messages
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.serializers.workflows.events import (
    WorkflowEventSerializer,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_kickoff_field,
    create_test_owner,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_partial_update__name__emit_workflow_update(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/{workflow.id}',
        data={'name': 'Renamed workflow'},
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.WORKFLOW_UPDATE
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
    assert event.payload == {
        'workflow_name': 'Renamed workflow',
        'changed_fields': ['name'],
    }
    assert event.workflow_id == workflow.id
    assert event.task_id is None
    workflows_updated_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
    )


def test_partial_update__kickoff__emit_sorted_kickoff_fields(
    mocker,
    api_client,
    fake_stream,
):

    """ Api names of the fields sent, never their values. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    create_test_kickoff_field(
        workflow=workflow,
        name='Last name',
        api_name='last-name',
    )
    create_test_kickoff_field(
        workflow=workflow,
        name='First name',
        api_name='first-name',
    )
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/{workflow.id}',
        data={
            'kickoff': {
                'last-name': 'Doe',
                'first-name': 'John',
            },
        },
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.WORKFLOW_UPDATE
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
    assert event.payload == {
        'workflow_name': workflow.name,
        'changed_fields': ['kickoff'],
        'kickoff_fields': ['first-name', 'last-name'],
    }
    assert event.workflow_id == workflow.id
    assert event.task_id is None
    workflows_updated_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
    )


def test_partial_update__due_date__emit_workflow_update(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    due_date = timezone.now() + timedelta(days=1)
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/{workflow.id}',
        data={'due_date_tsp': due_date.timestamp()},
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.WORKFLOW_UPDATE
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
    assert event.payload == {
        'workflow_name': workflow.name,
        'changed_fields': ['due_date'],
    }
    assert event.workflow_id == workflow.id
    assert event.task_id is None
    workflows_updated_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
    )


def test_partial_update__all_fields__changed_fields_in_fixed_order(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    create_test_kickoff_field(
        workflow=workflow,
        name='Client',
        api_name='client',
    )
    due_date = timezone.now() + timedelta(days=1)
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    workflows_urgent_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_urgent',
    )
    send_urgent_notification_mock = mocker.patch(
        'src.notifications.tasks.send_urgent_notification.delay',
    )
    send_event_created_mock = mocker.patch(
        'src.processes.services.events.send_event_created.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/{workflow.id}',
        data={
            'kickoff': {'client': 'Acme'},
            'is_urgent': True,
            'due_date_tsp': due_date.timestamp(),
            'name': 'Renamed workflow',
        },
    )

    # assert
    assert response.status_code == 200
    urgent_event = WorkflowEvent.objects.get(
        workflow=workflow,
        type=WorkflowEventType.URGENT,
    )
    assert len(fake_stream.events) == 2
    assert fake_stream.events[0][1].type == EventName.WORKFLOW_URGENT
    event = fake_stream.events[1][1]
    assert event.type == EventName.WORKFLOW_UPDATE
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
    assert event.payload == {
        'workflow_name': 'Renamed workflow',
        'changed_fields': ['name', 'due_date', 'is_urgent', 'kickoff'],
        'kickoff_fields': ['client'],
    }
    assert event.workflow_id == workflow.id
    assert event.task_id is None
    workflows_updated_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
    )
    workflows_urgent_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
        action=WorkflowActions.marked,
    )
    send_urgent_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        author_id=owner.id,
        task_ids=[task.id],
        account_id=account.id,
    )
    send_event_created_mock.assert_called_once_with(
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        account_id=account.id,
        data=WorkflowEventSerializer(instance=urgent_event).data,
    )


def test_partial_update__is_urgent__workflow_urgent_then_update(
    mocker,
    api_client,
    fake_stream,
):

    """ The urgent mark leaves its own workflow event: the stream holds
        workflow.urgent first and workflow.update after it. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    workflows_urgent_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_urgent',
    )
    send_urgent_notification_mock = mocker.patch(
        'src.notifications.tasks.send_urgent_notification.delay',
    )
    send_event_created_mock = mocker.patch(
        'src.processes.services.events.send_event_created.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/{workflow.id}',
        data={'is_urgent': True},
    )

    # assert
    assert response.status_code == 200
    urgent_event = WorkflowEvent.objects.get(
        workflow=workflow,
        type=WorkflowEventType.URGENT,
    )
    assert len(fake_stream.events) == 2
    assert fake_stream.events[0][1].type == EventName.WORKFLOW_URGENT
    event = fake_stream.events[1][1]
    assert event.type == EventName.WORKFLOW_UPDATE
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
    assert event.payload == {
        'workflow_name': workflow.name,
        'changed_fields': ['is_urgent'],
    }
    assert event.workflow_id == workflow.id
    assert event.task_id is None
    workflows_updated_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
    )
    workflows_urgent_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
        action=WorkflowActions.marked,
    )
    send_urgent_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        author_id=owner.id,
        task_ids=[task.id],
        account_id=account.id,
    )
    send_event_created_mock.assert_called_once_with(
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        account_id=account.id,
        data=WorkflowEventSerializer(instance=urgent_event).data,
    )


def test_partial_update__unmark_urgent__not_urgent_then_update(
    mocker,
    api_client,
    fake_stream,
):

    """ Dropping the urgent mark leaves its own workflow event too:
        the stream holds workflow.not_urgent before workflow.update. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        is_urgent=True,
    )
    task = workflow.tasks.get(number=1)
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    workflows_urgent_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_urgent',
    )
    send_not_urgent_notification_mock = mocker.patch(
        'src.notifications.tasks.send_not_urgent_notification.delay',
    )
    send_event_created_mock = mocker.patch(
        'src.processes.services.events.send_event_created.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/{workflow.id}',
        data={'is_urgent': False},
    )

    # assert
    assert response.status_code == 200
    not_urgent_event = WorkflowEvent.objects.get(
        workflow=workflow,
        type=WorkflowEventType.NOT_URGENT,
    )
    assert len(fake_stream.events) == 2
    assert fake_stream.events[0][1].type == EventName.WORKFLOW_NOT_URGENT
    event = fake_stream.events[1][1]
    assert event.type == EventName.WORKFLOW_UPDATE
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
    assert event.payload == {
        'workflow_name': workflow.name,
        'changed_fields': ['is_urgent'],
    }
    assert event.workflow_id == workflow.id
    assert event.task_id is None
    workflows_updated_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
    )
    workflows_urgent_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
        action=WorkflowActions.unmarked,
    )
    send_not_urgent_notification_mock.assert_called_once_with(
        author_id=owner.id,
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        task_ids=[task.id],
        account_id=account.id,
    )
    send_event_created_mock.assert_called_once_with(
        logging=account.log_api_requests,
        logo_lg=account.logo_lg,
        account_id=account.id,
        data=WorkflowEventSerializer(instance=not_urgent_event).data,
    )


def test_partial_update__same_is_urgent__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        is_urgent=False,
    )
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    workflows_urgent_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_urgent',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/{workflow.id}',
        data={'is_urgent': False},
    )

    # assert
    assert response.status_code == 200
    assert fake_stream.events == []
    workflows_updated_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
    )
    workflows_urgent_mock.assert_not_called()


def test_partial_update__same_name_template__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        name='Onboarding',
        name_template='Onboarding',
    )
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/{workflow.id}',
        data={'name': 'Onboarding'},
    )

    # assert
    assert response.status_code == 200
    assert fake_stream.events == []
    workflows_updated_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
    )


def test_partial_update__empty_kickoff__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/{workflow.id}',
        data={'kickoff': {}},
    )

    # assert
    assert response.status_code == 200
    assert fake_stream.events == []
    workflows_updated_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
    )


def test_partial_update__empty_body__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(f'/workflows/{workflow.id}', data={})

    # assert
    assert response.status_code == 200
    assert fake_stream.events == []
    workflows_updated_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
    )


def test_partial_update__due_date_in_past__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    due_date = timezone.now() - timedelta(days=1)
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/{workflow.id}',
        data={'due_date_tsp': due_date.timestamp()},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PW_0051
    assert response.data['details']['name'] == 'due_date_tsp'
    assert response.data['details']['reason'] == messages.MSG_PW_0051
    assert fake_stream.events == []
    workflows_updated_mock.assert_not_called()
