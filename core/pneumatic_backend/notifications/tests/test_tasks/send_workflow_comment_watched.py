import pytest
from django.utils import timezone
from pneumatic_backend.processes.enums import (
    WorkflowEventActionType
)
from pneumatic_backend.processes.models import (
    WorkflowEventAction,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_account,
)
from pneumatic_backend.notifications.tasks import (
    _send_workflow_comment_watched
)
from pneumatic_backend.processes.api_v2.serializers.workflow.events import (
    WorkflowEventSerializer,
)
from pneumatic_backend.processes.api_v2.services.events import (
    WorkflowEventService
)


pytestmark = pytest.mark.django_db


def test_send_workflow_comment_watched__not_watched__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    comment_event = WorkflowEventService.comment_created_event(
        user=account_owner,
        workflow=workflow,
        text='text',
        after_create_actions=False
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_workflow_event'
    )

    # act
    _send_workflow_comment_watched()

    # assert
    comment_event.refresh_from_db()
    data = WorkflowEventSerializer(instance=comment_event).data
    assert comment_event.watched == []
    assert data['watched'] == []
    send_workflow_event_mock.assert_not_called()


def test_send_workflow_comment_watched__first_watched__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    user = create_test_user(
        email='test@test.test',
        account=account,
        is_account_owner=False
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    comment_event = WorkflowEventService.comment_created_event(
        user=account_owner,
        workflow=workflow,
        text='text',
        after_create_actions=False
    )

    event_action = WorkflowEventAction.objects.create(
        user=user,
        event=comment_event,
        type=WorkflowEventActionType.WATCHED
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_workflow_event'
    )

    # act
    _send_workflow_comment_watched()

    # assert
    comment_event.refresh_from_db()
    data = WorkflowEventSerializer(instance=comment_event).data
    assert not WorkflowEventAction.objects.filter(id=event_action.id).exists()
    assert len(comment_event.watched) == 1
    assert comment_event.watched[0]['date'] is not None
    assert comment_event.watched[0]['user_id'] == user.id
    assert len(data['watched']) == 1
    assert type(data['watched'][0]['date_tsp']) is float
    assert data['watched'][0]['date'] is not None
    assert data['watched'][0]['user_id'] == user.id
    send_workflow_event_mock.assert_called_once_with(data)


def test_send_workflow_comment_watched__second_watched__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    user = create_test_user(
        email='test@test.test',
        account=account,
        is_account_owner=False
    )
    user_2 = create_test_user(
        email='test2@test.test',
        account=account,
        is_account_owner=False
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    comment_event = WorkflowEventService.comment_created_event(
        user=account_owner,
        workflow=workflow,
        text='text',
        after_create_actions=False
    )
    comment_event.watched = [
        {
            'date':  timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'date_tsp':  timezone.now().timestamp(),
            'user_id': user_2.id
        }
    ]
    comment_event.save()

    event_action = WorkflowEventAction.objects.create(
        user=user,
        event=comment_event,
        type=WorkflowEventActionType.WATCHED
    )
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_workflow_event'
    )

    # act
    _send_workflow_comment_watched()

    # assert
    comment_event.refresh_from_db()
    data = WorkflowEventSerializer(instance=comment_event).data
    assert not WorkflowEventAction.objects.filter(id=event_action.id).exists()
    assert len(comment_event.watched) == 2
    assert comment_event.watched[0]['date'] is not None
    assert type(comment_event.watched[0]['date_tsp']) is float
    assert comment_event.watched[0]['user_id'] == user.id
    assert comment_event.watched[1]['date'] is not None
    assert type(comment_event.watched[1]['date_tsp']) is float
    assert comment_event.watched[1]['user_id'] == user_2.id
    assert len(data['watched']) == 2
    send_workflow_event_mock.assert_called_once_with(data)
