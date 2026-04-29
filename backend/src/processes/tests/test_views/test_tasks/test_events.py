import pytest
from django.contrib.auth import get_user_model

from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.enums import WorkflowEventType, FieldType
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.fieldset import FieldSet
from src.processes.models.workflows.task import TaskPerformer
from src.processes.services.events import (
    WorkflowEventService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_attachment,
    create_test_event,
    create_test_guest,
    create_test_owner,
    create_test_user,
    create_test_workflow, create_test_dataset,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db
datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'


def test_events__empty_list__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v2/tasks/{task.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_events__by_task__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2, active_task_number=2)
    task_1 = workflow.tasks.get(number=1)
    event = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.TASK_COMPLETE,
    )
    create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.TASK_START,
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
        type_event=WorkflowEventType.TASK_COMPLETE,
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
        is_admin=True,
    )
    workflow.members.add(user)
    event = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.TASK_COMPLETE,
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
        is_admin=False,
    )
    workflow.members.add(user)
    event = create_test_event(
        workflow=workflow,
        user=account_owner,
        type_event=WorkflowEventType.TASK_COMPLETE,
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
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )
    WorkflowEventService.task_complete_event(task=task, user=account_owner)

    # act
    response = api_client.get(
        f'/v2/tasks/{task.id}/events',
        **{'X-Guest-Authorization': str_token},
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
        user_id=guest_1.id,
    )
    GuestJWTAuthService.get_str_token(
        task_id=task_1.id,
        user_id=guest_1.id,
        account_id=account.id,
    )

    workflow_2 = create_test_workflow(account_owner, tasks_count=1)
    task_2 = workflow_2.tasks.get(number=1)
    guest_2 = create_test_guest(
        account=account,
        email='guest2@test.test',
    )
    TaskPerformer.objects.create(
        task_id=task_2.id,
        user_id=guest_2.id,
    )
    str_token_2 = GuestJWTAuthService.get_str_token(
        task_id=task_2.id,
        user_id=guest_2.id,
        account_id=account.id,
    )

    # act
    response = api_client.get(
        f'/v2/tasks/{task_1.id}/events',
        **{'X-Guest-Authorization': str_token_2},
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
    task = workflow.tasks.get(number=1)
    WorkflowEventService.comment_created_event(
        text='Comment 1',
        task=task,
        user=user,
        after_create_actions=False,
    )
    WorkflowEventService.comment_created_event(
        text='Comment 2',
        task=task,
        user=user,
        after_create_actions=False,
    )
    WorkflowEventService.task_complete_event(task=task, user=user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/v2/tasks/{task.id}/events?limit=1&offset=1',
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
    task = workflow.tasks.get(number=1)
    create_test_event(
        workflow=workflow,
        user=user,
        type_event=type_event,
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
    task = workflow.tasks.get(number=1)
    create_test_event(
        workflow=workflow,
        user=user,
        type_event=type_event,
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
    task = workflow.tasks.get(number=1)
    task.save()
    event_1 = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.COMMENT,
    )
    event_2 = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.URGENT,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/v2/tasks/{task.id}/events?ordering=-created',
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
    task = workflow.tasks.get(number=1)
    event_1 = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.COMMENT,
    )
    event_2 = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.URGENT,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/v2/tasks/{task.id}/events?ordering=created',
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
    task = workflow.tasks.get(number=1)
    event_1 = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.COMMENT,
    )
    create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.COMMENT,
    )
    create_test_attachment(
        workflow=workflow,
        account=user.account,
        event=event_1,
    )

    # act
    response = api_client.get(
        f'/v2/tasks/{task.id}/events?only_attachments=true',
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
    task = workflow.tasks.get(number=1)
    create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.COMMENT,
    )
    event_2 = create_test_event(
        workflow=workflow,
        user=user,
        type_event=WorkflowEventType.TASK_REVERT,
    )

    # act
    response = api_client.get(
        f'/v2/tasks/{task.id}/events?include_comments=false',
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
    task = workflow.tasks.get(number=1)

    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    event = create_test_event(
        workflow=workflow,
        user=account_owner,
        type_event=WorkflowEventType.COMMENT,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )

    # act
    response = api_client.get(
        f'/v2/tasks/{task.id}/events',
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == event.id


def test_events__user_is_member_in_deleted_task__not_found(api_client):

    # arrange
    user = create_test_owner()
    admin = create_test_admin(account=user.account)
    api_client.token_authenticate(admin)
    workflow = create_test_workflow(user, tasks_count=1)
    workflow.members.add(admin)
    task = workflow.tasks.get(number=1)
    task.delete()

    # act
    response = api_client.get(f'/v2/tasks/{task.id}/events')

    # assert
    assert response.status_code == 404


def test_events__user_is_not_member_in_deleted_task__not_found(api_client):

    # arrange
    user = create_test_owner()
    admin = create_test_admin(account=user.account)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.delete()
    api_client.token_authenticate(admin)

    # act
    response = api_client.get(f'/v2/tasks/{task.id}/events')

    # assert
    assert response.status_code == 404


def test_events__task_complete_with_dataset__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=1)
    dataset_item = dataset.items.get(order=1)
    workflow = create_test_workflow(user, tasks_count=2, active_task_number=2)
    task = workflow.tasks.get(number=1)
    field = TaskField.objects.create(
        type=FieldType.CHECKBOX,
        name='checkbox',
        task=task,
        value=dataset_item.value,
        workflow=workflow,
        account=account,
        dataset=dataset,
    )

    event = create_test_event(
        workflow=workflow,
        task=task,
        user=user,
        type_event=WorkflowEventType.TASK_COMPLETE,
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/v2/tasks/{task.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    event_data = response.data[0]

    assert event_data['id'] == event.id
    assert event_data['type'] == WorkflowEventType.TASK_COMPLETE
    task_data = event_data['task']
    assert len(task_data['output']) == 1
    field_data = task_data['output'][0]
    assert field_data['id'] == field.id
    assert field_data['type'] == field.type
    assert field_data['is_required'] == field.is_required
    assert field_data['name'] == field.name
    assert field_data['description'] == field.description
    assert field_data['api_name'] == field.api_name
    assert field_data['value'] == dataset_item.value
    assert field_data['order'] == field.order


def test_events__task_complete_fieldsets_present__ok(api_client):

    """
    GET task events: TASK_COMPLETE row includes non-null task.fieldsets when
    the task has at least one FieldSet.
    """

    # arrange

    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task_1 = workflow.tasks.get(number=1)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        task=task_1,
        name='Fieldset 1',
        order=1,
    )
    field_1 = TaskField.objects.create(
        account=account,
        workflow=workflow,
        task=task_1,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.TEXT,
        order=1,
    )
    field_2 = TaskField.objects.create(
        account=account,
        workflow=workflow,
        task=task_1,
        fieldset=fieldset,
        name='Field 2',
        type=FieldType.NUMBER,
        order=2,
    )
    WorkflowEventService.task_complete_event(
        task=task_1,
        user=user,
        after_create_actions=False,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=f'/v2/tasks/{task_1.id}/events',
    )

    # assert
    assert response.status_code == 200
    event_data = response.data[0]
    assert event_data['type'] == WorkflowEventType.TASK_COMPLETE
    fieldsets_data = event_data['task']['fieldsets']
    assert fieldsets_data is not None
    assert len(fieldsets_data) == 1
    fieldset.refresh_from_db()
    field_1.refresh_from_db()
    field_2.refresh_from_db()
    fieldset_data = fieldsets_data[0]
    assert fieldset_data['id'] == fieldset.id
    assert fieldset_data['api_name'] == fieldset.api_name
    assert fieldset_data['name'] == fieldset.name
    assert fieldset_data['description'] == fieldset.description
    assert fieldset_data['order'] == fieldset.order
    assert fieldset_data['label_position'] == fieldset.label_position
    assert fieldset_data['layout'] == fieldset.layout
    fields_data = fieldset_data['fields']
    assert len(fields_data) == 2
    field_2_data = fields_data[0]
    assert field_2_data['id'] == field_2.id
    assert field_2_data['order'] == field_2.order
    assert field_2_data['type'] == field_2.type
    assert field_2_data['is_required'] == field_2.is_required
    assert field_2_data['is_hidden'] == field_2.is_hidden
    assert field_2_data['description'] == field_2.description
    assert field_2_data['api_name'] == field_2.api_name
    assert field_2_data['name'] == field_2.name
    assert field_2_data['value'] == field_2.value
    assert field_2_data['markdown_value'] == field_2.markdown_value
    assert field_2_data['clear_value'] == field_2.clear_value
    assert field_2_data['user_id'] == field_2.user_id
    assert field_2_data['group_id'] == field_2.group_id
    assert field_2_data['selections'] == []
    assert field_2_data['attachments'] == []
    field_1_data = fields_data[1]
    assert field_1_data['id'] == field_1.id


def test_events__task_complete_fieldsets_absent__ok(api_client):

    """
    GET task events: TASK_COMPLETE row has task.fieldsets equal to null when
    the task has no FieldSet rows.
    """

    # arrange

    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task_1 = workflow.tasks.get(number=1)
    WorkflowEventService.task_complete_event(
        task=task_1,
        user=user,
        after_create_actions=False,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=f'/v2/tasks/{task_1.id}/events',
    )

    # assert

    assert response.status_code == 200
    item_1 = response.data[0]
    assert item_1['type'] == WorkflowEventType.TASK_COMPLETE
    task_payload = item_1['task']
    assert task_payload['fieldsets'] is None


def test_events__non_complete_task_fieldsets_null__ok(api_client):

    """
    GET task events: non-TASK_COMPLETE event exposes task.fieldsets as null.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task_1 = workflow.tasks.get(number=1)
    create_test_event(
        workflow=workflow,
        user=user,
        task=task_1,
        type_event=WorkflowEventType.COMMENT,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=f'/v2/tasks/{task_1.id}/events',
    )

    # assert
    assert response.status_code == 200
    item_1 = response.data[0]
    assert item_1['type'] == WorkflowEventType.COMMENT
    task_payload = item_1['task']
    assert task_payload['fieldsets'] is None
