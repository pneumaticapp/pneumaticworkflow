import pytest
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.api_v2.services import (
    WorkflowEventService,
)
from pneumatic_backend.processes.models import TaskPerformer

from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_account,
    create_test_guest,
    create_test_event, create_test_attachment
)
from pneumatic_backend.processes.enums import WorkflowEventType
from pneumatic_backend.authentication.services import GuestJWTAuthService

UserModel = get_user_model()
pytestmark = pytest.mark.django_db
datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'


def test_events__empty_list__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.current_task_instance
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v2/tasks/{task.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_events__by_task__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    event = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.TASK_COMPLETE
    )
    workflow.current_task = 2
    workflow.save()
    create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.TASK_START
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v2/tasks/{task_1.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == event.id
    assert response.data[0]['type'] == WorkflowEventType.TASK_COMPLETE


def test_events__account_owner__ok(api_client):

    # arrange
    user = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(user, tasks_count=1)
    task_1 = workflow.tasks.get(number=1)
    event = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.TASK_COMPLETE
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v2/tasks/{task_1.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == event.id


def test_events__admin__ok(api_client):

    # arrange
    account_owner = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task_1 = workflow.tasks.get(number=1)
    user = create_test_user(
        account=account_owner.account,
        email='test@test.com',
        is_account_owner=False,
        is_admin=True
    )
    workflow.members.add(user)
    event = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.TASK_COMPLETE
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v2/tasks/{task_1.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == event.id


def test_events__not_admin__ok(api_client):

    # arrange
    account_owner = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task_1 = workflow.tasks.get(number=1)
    user = create_test_user(
        account=account_owner.account,
        email='test@test.com',
        is_account_owner=False,
        is_admin=False
    )
    workflow.members.add(user)
    event = create_test_event(
        workflow=workflow,
        user=account_owner,
        type_event=WorkflowEventType.TASK_COMPLETE
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v2/tasks/{task_1.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == event.id


def test_events__guest_user__ok(api_client, mocker):
    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id
    )
    WorkflowEventService.task_complete_event(task=task, user=account_owner)

    # act
    response = api_client.get(
        f'/v2/tasks/{task.id}/events',
        **{'X-Guest-Authorization': str_token}
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['type'] == WorkflowEventType.TASK_COMPLETE


def test_events__guest_from_another_task__permission_denied(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    workflow_1 = create_test_workflow(account_owner, tasks_count=1)
    task_1 = workflow_1.tasks.get(number=1)
    guest_1 = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task_id=task_1.id,
        user_id=guest_1.id
    )
    GuestJWTAuthService.get_str_token(
        task_id=task_1.id,
        user_id=guest_1.id,
        account_id=account.id
    )

    workflow_2 = create_test_workflow(account_owner, tasks_count=1)
    task_2 = workflow_2.tasks.get(number=1)
    guest_2 = create_test_guest(
        account=account,
        email='guest2@test.test'
    )
    TaskPerformer.objects.create(
        task_id=task_2.id,
        user_id=guest_2.id
    )
    str_token_2 = GuestJWTAuthService.get_str_token(
        task_id=task_2.id,
        user_id=guest_2.id,
        account_id=account.id
    )

    # act
    response = api_client.get(
        f'/v2/tasks/{task_1.id}/events',
        **{'X-Guest-Authorization': str_token_2}
    )

    # assert
    assert response.status_code == 403


def test_events__not_exist__not_found(api_client):
    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v2/tasks/999999/events')

    # assert
    assert response.status_code == 404


def test_events__pagination__ok(api_client):
    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.current_task_instance
    WorkflowEventService.comment_created_event(
        text='Comment 1',
        task=task,
        user=user,
        after_create_actions=False
    )
    WorkflowEventService.comment_created_event(
        text='Comment 2',
        task=task,
        user=user,
        after_create_actions=False
    )
    WorkflowEventService.task_complete_event(task=task, user=user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/v2/tasks/{task.id}/events?limit=1&offset=1'
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['count'] == 3
    assert len(response_data['results']) == 1
    assert response_data['next'] is not None
    assert response_data['previous'] is not None
    assert response.data['results'][0]['type'] == WorkflowEventType.COMMENT
    assert response.data['results'][0]['text'] == 'Comment 2'


@pytest.mark.parametrize(
    "type_event",
    [
        WorkflowEventType.TASK_COMPLETE,
        WorkflowEventType.TASK_REVERT,
        WorkflowEventType.COMMENT,
        WorkflowEventType.TASK_PERFORMER_CREATED,
        WorkflowEventType.TASK_PERFORMER_DELETED,
        WorkflowEventType.TASK_PERFORMER_GROUP_CREATED,
        WorkflowEventType.TASK_PERFORMER_GROUP_DELETED,
        WorkflowEventType.DUE_DATE_CHANGED,
        WorkflowEventType.REVERT,
        WorkflowEventType.URGENT,
        WorkflowEventType.NOT_URGENT,
        WorkflowEventType.SUB_WORKFLOW_RUN,
    ],
)
def test_events__allowed_events_type__ok(api_client, type_event):
    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.current_task_instance
    create_test_event(
        workflow=workflow,
        user=user,
        type_event=type_event
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v2/tasks/{task.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['type'] == type_event


@pytest.mark.parametrize(
    "type_event",
    [
        WorkflowEventType.TASK_START,
        WorkflowEventType.RUN,
        WorkflowEventType.COMPLETE,
        WorkflowEventType.ENDED,
        WorkflowEventType.DELAY,
        WorkflowEventType.ENDED_BY_CONDITION,
        WorkflowEventType.FORCE_RESUME,
        WorkflowEventType.FORCE_DELAY,
        WorkflowEventType.TASK_SKIP,
        WorkflowEventType.TASK_SKIP_NO_PERFORMERS,
    ],
)
def test_events__disallow_type_event__not_show(api_client, type_event):
    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.current_task_instance
    create_test_event(
        workflow=workflow,
        user=user,
        type_event=type_event
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v2/tasks/{task.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_events__ordering_date_inverted__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.current_task_instance
    task.save()
    event_1 = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.COMMENT
    )
    event_2 = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.URGENT
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/v2/tasks/{task.id}/events?ordering=-created'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == event_2.id
    assert response.data[1]['id'] == event_1.id


def test_events__ordering_date__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.current_task_instance
    event_1 = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.COMMENT
    )
    event_2 = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.URGENT
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/v2/tasks/{task.id}/events?ordering=created'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == event_1.id
    assert response.data[1]['id'] == event_2.id


def test_events__filter_only_attachments__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.current_task_instance
    event_1 = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.COMMENT
    )
    create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.COMMENT
    )
    create_test_attachment(
        workflow=workflow,
        account=user.account,
        event=event_1
    )

    # act
    response = api_client.get(
        f'/v2/tasks/{task.id}/events?only_attachments=true'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == event_1.id


def test_events__filter_exclude_comments__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.current_task_instance
    create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.COMMENT
    )
    event_2 = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.TASK_REVERT
    )

    # act
    response = api_client.get(
        f'/v2/tasks/{task.id}/events?include_comments=false'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == event_2.id


def test_events__guest__ok(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance

    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id
    )
    event = create_test_event(
        workflow=workflow,
        user=account_owner,
        type_event=WorkflowEventType.COMMENT
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id
    )

    # act
    response = api_client.get(
        f'/v2/tasks/{task.id}/events',
        **{'X-Guest-Authorization': str_token}
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == event.id
