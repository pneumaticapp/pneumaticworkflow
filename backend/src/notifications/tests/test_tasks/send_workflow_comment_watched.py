import pytest
from django.utils import timezone
from src.processes.enums import (
    WorkflowEventActionType
)
from src.processes.models import (
    WorkflowEventAction,
)
from src.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_account,
)
from src.notifications.tasks import (
    _send_workflow_comment_watched
)
from src.processes.serializers.workflows.events import (
    WorkflowEventSerializer,
)
from src.processes.services.events import (
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
        task=workflow.tasks.get(number=1),
        text='text',
        after_create_actions=False
    )
    send_workflow_event_mock = mocker.patch(
        'src.notifications.tasks._send_workflow_event'
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
    account = create_test_account(logo_lg='https://logo.jpg')
    account_owner = create_test_user(account=account)
    user = create_test_user(
        email='test@test.test',
        account=account,
        is_account_owner=False
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    comment_event = WorkflowEventService.comment_created_event(
        user=account_owner,
        task=workflow.tasks.get(number=1),
        text='text',
        after_create_actions=False
    )

    event_action = WorkflowEventAction.objects.create(
        user=user,
        event=comment_event,
        type=WorkflowEventActionType.WATCHED
    )
    send_workflow_event_mock = mocker.patch(
        'src.notifications.tasks._send_workflow_event'
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
    send_workflow_event_mock.assert_called_once_with(
        data=data,
        account_id=account.id,
        logo_lg=account.logo_lg
    )


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
        task=workflow.tasks.get(number=1),
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
        'src.notifications.tasks._send_workflow_event'
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
    send_workflow_event_mock.assert_called_once_with(
        data=data,
        account_id=account.id,
        logo_lg=account.logo_lg
    )
