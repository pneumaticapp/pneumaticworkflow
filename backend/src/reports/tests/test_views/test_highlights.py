from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from src.authentication.enums import AuthTokenType
from src.generics.messages import (
    MSG_GE_0003,
    MSG_GE_0007,
    MSG_GE_0020,
)
from src.processes.enums import (
    FieldType,
    WorkflowEventType,
)
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.task import Delay
from src.processes.models.workflows.workflow import Workflow
from src.processes.services.events import (
    WorkflowEventService,
)
from src.processes.services.tasks.performers import (
    TaskPerformersService,
)
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_group,
    create_test_template,
    create_test_user,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test__ordering__ok(api_client):
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    workflow = create_test_workflow(user, tasks_count=3, active_task_number=2)
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)

    WorkflowEventService.task_complete_event(
        task=task_1,
        user=user,
        after_create_actions=False,
    )
    task_2.date_started = timezone.now()
    task_2.save(update_fields=['date_started'])
    WorkflowEventService.comment_created_event(
        text='comment',
        task=task_2,
        user=user,
        after_create_actions=False,
    )

    api_client.token_authenticate(user)
    response = api_client.get('/reports/highlights')

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['type'] == WorkflowEventType.COMMENT


def test__return_task__ok(api_client, mocker):

    # arrange
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    workflow = create_test_workflow(user)
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    text_comment = 'text_comment'
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': task_1.id,
        },
    )
    api_client.post(
        f'/v2/tasks/{task_2.id}/revert',
        data={
            'comment': text_comment,
        },
    )

    # act
    response = api_client.get('/reports/highlights')

    # assert
    assert response.status_code == 200

    assert len(response.data) == 1
    event_data = response.data[0]
    assert event_data['type'] == WorkflowEventType.TASK_REVERT
    assert event_data['created'] is not None
    assert event_data['text'] == text_comment
    assert type(event_data['created_tsp']) is float


def test__return_to_task__ok(api_client, mocker):

    # arrange
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_completed_webhook.delay',
    )
    mocker.patch(
        'src.processes.tasks.webhooks.'
        'send_task_returned_webhook.delay',
    )
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': task.id,
        },
    )
    api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task': workflow.tasks.get(number=1).id},
    )

    # act
    response = api_client.get(
        '/reports/highlights',
    )

    # assert
    assert response.status_code == 200

    assert len(response.data) == 1
    assert response.data[0]['type'] == WorkflowEventType.REVERT


def test_highlights_start_workflow(api_client):
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )

    workflow = create_test_workflow(user, tasks_count=3, active_task_number=2)
    other_workflow = create_test_workflow(user)
    WorkflowEventService.workflow_run_event(other_workflow)
    task_1 = workflow.tasks.get(number=1)
    WorkflowEventService.task_complete_event(
        task=task_1,
        user=user,
        after_create_actions=False,
    )
    task_2 = workflow.tasks.get(number=2)
    task_2.date_started = timezone.now()
    task_2.save(update_fields=['date_started'])
    WorkflowEventService.comment_created_event(
        text='Revert',
        task=task_1,
        user=user,
        after_create_actions=False,
    )
    api_client.token_authenticate(user)

    response = api_client.get('/reports/highlights')

    assert response.status_code == 200

    assert len(response.data) == 2
    assert response.data[0]['type'] == WorkflowEventType.COMMENT
    assert response.data[1]['type'] == WorkflowEventType.RUN
    assert response.data[1]['workflow']['is_external'] is False


def test_highlights__used_tsp__ok(api_client):
    user = create_test_user()

    workflow = create_test_workflow(user, tasks_count=3, active_task_number=2)
    WorkflowEventService.workflow_run_event(workflow)
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    WorkflowEventService.task_started_event(
        task=task_1,
        after_create_actions=False,
    )
    WorkflowEventService.task_complete_event(
        task=task_1,
        user=user,
        after_create_actions=False,
    )
    WorkflowEventService.task_started_event(
        task=task_2,
        after_create_actions=False,
    )
    task_2.date_started = timezone.now() + timedelta(hours=10)
    task_2.save(update_fields=['date_started'])
    WorkflowEventService.comment_created_event(
        text='Revert',
        task=task_1,
        user=user,
        after_create_actions=False,
    )

    workflow_2 = create_test_workflow(
        user,
        tasks_count=3,
        active_task_number=2,
    )
    task_21 = workflow_2.tasks.get(number=1)
    WorkflowEventService.task_started_event(
        task=task_21,
        after_create_actions=False,
    )
    event = WorkflowEvent.objects.get(
        type=WorkflowEventType.TASK_START,
        task_json__id=task_21.id,
    )
    event.created = timezone.now() + timedelta(hours=7)
    event.save()
    WorkflowEventService.task_complete_event(
        task=task_21,
        user=user,
        after_create_actions=False,
    )

    date_end_period = timezone.now()
    workflow_outside = create_test_workflow(
        user,
        tasks_count=3,
        active_task_number=2,
    )
    task_31 = workflow_outside.tasks.get(number=1)
    WorkflowEventService.task_started_event(
        task=task_31,
        after_create_actions=False,
    )
    event = WorkflowEvent.objects.get(
        type=WorkflowEventType.TASK_START,
        task_json__id=task_31.id,
    )
    event.created = timezone.now() + timedelta(hours=7)
    event.save()
    WorkflowEventService.task_complete_event(
        task=task_31,
        user=user,
        after_create_actions=False,
    )

    date_after_tsp = (timezone.now() - timedelta(hours=1)).timestamp()
    date_before_tsp = date_end_period.timestamp()
    api_client.token_authenticate(user)

    response = api_client.get(
        '/reports/highlights',
        data={
            'date_after_tsp': date_after_tsp,
            'date_before_tsp': date_before_tsp,
        },
    )

    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['type'] == WorkflowEventType.TASK_COMPLETE
    assert response.data[1]['type'] == WorkflowEventType.COMMENT


@pytest.mark.parametrize('date_before_tsp', (' ', 'test', '01/02/2023'))
def test_highlights__invalid_value_tsp__validation_error(
    api_client,
    date_before_tsp,
):
    user = create_test_user()
    date_after = timezone.now() - timedelta(hours=1)
    api_client.token_authenticate(user)

    response = api_client.get(
        '/reports/highlights',
        data={
            'date_after_tsp': date_after.timestamp(),
            'date_before_tsp': date_before_tsp,
        },
    )

    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_GE_0007
    assert response.data['details']['reason'] == MSG_GE_0007
    assert response.data['details']['name'] == 'date_before_tsp'


def test_highlights__tcp_in_milliseconds__validation_error(api_client):
    user = create_test_user()
    date_after = timezone.now() - timedelta(hours=1)
    date_before = timezone.now() + timedelta(days=1)
    api_client.token_authenticate(user)

    response = api_client.get(
        '/reports/highlights',
        data={
            'date_before_tsp': date_before.timestamp(),
            'date_after_tsp': date_after.timestamp() * 1000,
        },
    )

    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_GE_0020
    assert response.data['details']['reason'] == MSG_GE_0020
    assert response.data['details']['name'] == 'date_after_tsp'


def test_highlights_by_template(api_client):
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    workflow_1 = create_test_workflow(user)
    workflow_2 = create_test_workflow(user)
    workflow_3 = create_test_workflow(user)

    WorkflowEventService.comment_created_event(
        user=user,
        text='Comment 1',
        task=workflow_1.tasks.get(number=1),
        after_create_actions=False,
    )
    event_2 = WorkflowEventService.comment_created_event(
        user=user,
        text='Comment 2',
        task=workflow_2.tasks.get(number=1),
        after_create_actions=False,
    )
    event_3 = WorkflowEventService.comment_created_event(
        user=user,
        text='Comment 3',
        task=workflow_3.tasks.get(number=1),
        after_create_actions=False,
    )

    api_client.token_authenticate(user)

    response = api_client.get(
        f'/reports/highlights?templates={workflow_2.template.id},'
        f'{workflow_3.template.id}',
    )

    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['text'] == event_3.text
    assert response.data[1]['text'] == event_2.text


def test__terminated_workflow__not_show(api_client):
    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )

    workflow_1 = create_test_workflow(user)
    workflow_2 = create_test_workflow(user)
    workflow_3 = create_test_workflow(user)

    WorkflowEventService.comment_created_event(
        text='Comment 1',
        task=workflow_1.tasks.get(number=1),
        user=user,
        after_create_actions=False,
    )
    event_2 = WorkflowEventService.comment_created_event(
        text='Comment 2',
        task=workflow_2.tasks.get(number=1),
        user=user,
        after_create_actions=False,
    )
    WorkflowEventService.comment_created_event(
        text='Revert',
        task=workflow_3.tasks.get(number=1),
        user=user,
        after_create_actions=False,
    )
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow_3.id}/close',
    )
    endpoint = (
        f'/reports/highlights?'
        f'templates={workflow_2.template.id},'
        f'{workflow_3.template.id}'
    )

    response = api_client.get(endpoint)

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['text'] == event_2.text


def test_highlights__filter_current_performer_ids__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    first_invited = create_invited_user(user)
    second_invited = create_invited_user(user, 'test_n@pneumatic.app')

    workflow_1 = create_test_workflow(user)
    workflow_2 = create_test_workflow(user)
    workflow_3 = create_test_workflow(user)

    WorkflowEventService.comment_created_event(
        text='Comment 1',
        task=workflow_1.tasks.get(number=1),
        user=user,
        after_create_actions=False,
    )
    event_2 = WorkflowEventService.comment_created_event(
        text='Comment 2',
        task=workflow_2.tasks.get(number=1),
        user=first_invited,
        after_create_actions=False,
    )
    event_3 = WorkflowEventService.comment_created_event(
        text='Comment 3',
        task=workflow_3.tasks.get(number=1),
        user=second_invited,
        after_create_actions=False,
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/reports/highlights',
        data={
            'current_performer_ids': f'{first_invited.id},{second_invited.id}',
        },

    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['text'] == event_3.text
    assert response.data[1]['text'] == event_2.text


def test_highlights__not_unique_current_performer_and_performer_group_ids__ok(
    api_client,
):

    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    first_invited = create_invited_user(user)
    second_invited = create_invited_user(user, 'test_n@pneumatic.app')
    group = create_test_group(account, users=[first_invited, second_invited])
    workflow_1 = create_test_workflow(user)
    workflow_2 = create_test_workflow(user)
    workflow_3 = create_test_workflow(user)

    WorkflowEventService.comment_created_event(
        text='Comment 1',
        task=workflow_1.tasks.get(number=1),
        user=user,
        after_create_actions=False,
    )
    event_2 = WorkflowEventService.comment_created_event(
        text='Comment 2',
        task=workflow_2.tasks.get(number=1),
        user=first_invited,
        after_create_actions=False,
    )
    event_3 = WorkflowEventService.comment_created_event(
        text='Comment 3',
        task=workflow_3.tasks.get(number=1),
        user=second_invited,
        after_create_actions=False,
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/reports/highlights',
        data={
            'current_performer_ids': f'{first_invited.id},{second_invited.id}',
            'current_performer_group_ids': group.id,
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['text'] == event_3.text
    assert response.data[1]['text'] == event_2.text


def test__is_urgent_event__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user)
    WorkflowEventService.workflow_urgent_event(
        event_type=WorkflowEventType.URGENT,
        workflow=workflow,
        user=user,
        after_create_actions=False,
    )
    event = WorkflowEventService.workflow_urgent_event(
        event_type=WorkflowEventType.NOT_URGENT,
        workflow=workflow,
        user=user,
        after_create_actions=False,
    )

    # act
    response = api_client.get('/reports/highlights')

    # assert
    assert response.status_code == 200
    event_data = response.data[0]
    assert event_data['id'] == event.id
    assert event_data['created_tsp'] == event.created.timestamp()
    assert event_data['type'] == WorkflowEventType.NOT_URGENT


def test__is_not_urgent_event__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user)
    WorkflowEventService.workflow_urgent_event(
        event_type=WorkflowEventType.NOT_URGENT,
        workflow=workflow,
        user=user,
        after_create_actions=False,
    )
    event = WorkflowEventService.workflow_urgent_event(
        event_type=WorkflowEventType.URGENT,
        workflow=workflow,
        user=user,
        after_create_actions=False,
    )

    # act
    response = api_client.get('/reports/highlights')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    event_data = response.data[0]
    assert event_data['id'] == event.id
    assert event_data['created_tsp'] == event.created.timestamp()
    assert event_data['type'] == WorkflowEventType.URGENT


def test__performer_created_event__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    user_performer = create_test_user(
        email='t@t.t',
        account=user.account,
    )
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformersService.create_performer(
        user_key=user_performer.id,
        request_user=user,
        task=task,
        run_actions=False,
        current_url='/page',
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    WorkflowEventService.performer_created_event(
        task=task,
        user=user,
        performer=user_performer,
        after_create_actions=False,
    )

    # act
    response = api_client.get('/reports/highlights')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['type'] == (
        WorkflowEventType.TASK_PERFORMER_CREATED
    )
    assert response.data[0]['user_id'] == user.id
    assert response.data[0]['task']['id'] == task.id
    assert response.data[0]['target_user_id'] == user_performer.id


def test__performer_deleted_event__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    user_performer = create_test_user(
        email='t@t.t',
        account=user.account,
    )
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    WorkflowEventService.performer_deleted_event(
        user=user,
        task=task,
        performer=user_performer,
        after_create_actions=False,
    )

    # act
    response = api_client.get('/reports/highlights')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['type'] == (
        WorkflowEventType.TASK_PERFORMER_DELETED
    )
    assert response.data[0]['user_id'] == user.id
    assert response.data[0]['task']['id'] == task.id
    assert response.data[0]['target_user_id'] == user_performer.id


def test_highlights__filter_current_performer_group_ids__ok(api_client):
    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    first_invited = create_invited_user(user)
    second_invited = create_invited_user(user, 'test_n@pneumatic.app')
    group = create_test_group(account, users=[first_invited, second_invited])
    workflow_1 = create_test_workflow(user)
    workflow_2 = create_test_workflow(user)
    workflow_3 = create_test_workflow(user)

    WorkflowEventService.comment_created_event(
        text='Comment 1',
        task=workflow_1.tasks.get(number=1),
        user=user,
        after_create_actions=False,
    )
    event_2 = WorkflowEventService.comment_created_event(
        text='Comment 2',
        task=workflow_2.tasks.get(number=1),
        user=first_invited,
        after_create_actions=False,
    )
    event_3 = WorkflowEventService.comment_created_event(
        text='Comment 3',
        task=workflow_3.tasks.get(number=1),
        user=second_invited,
        after_create_actions=False,
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/reports/highlights',
        data={
            'current_performer_group_ids': group.id,
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['text'] == event_3.text
    assert response.data[1]['text'] == event_2.text


@pytest.mark.parametrize('current_performer_group_ids', ('', []))
def test_highlights__empty_current_performer_group_ids__ok(
    api_client, current_performer_group_ids,
):
    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    workflow = create_test_workflow(user)
    event = WorkflowEventService.comment_created_event(
        text='Comment 1',
        task=workflow.tasks.get(number=1),
        user=user,
        after_create_actions=False,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/reports/highlights',
        data={
            'current_performer_group_ids': current_performer_group_ids,
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['text'] == event.text


def test_highlights__invalid_current_performer_group_ids__validation_error(
    api_client,
):
    # arrange
    account = create_test_account()
    user = create_test_user(
        account=account,
        is_account_owner=True,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/reports/highlights',
        data={
            'current_performer_group_ids': 'invalid',
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_GE_0003
    assert response.data['details']['reason'] == MSG_GE_0003
    assert response.data['details']['name'] == 'current_performer_group_ids'


def test_highlights__current_performer_group_ids_deleted_group__ok(api_client):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    group = create_test_group(account, users=[user])
    group.delete()
    workflow = create_test_workflow(user)
    event = WorkflowEventService.comment_created_event(
        text='Comment 1',
        task=workflow.tasks.get(number=1),
        user=user,
        after_create_actions=False,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/reports/highlights',
        data={
            'current_performer_group_ids': group.id,
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['text'] == event.text


def test_highlights__current_performer_group_other_account_group__ok(
    api_client,
):
    # arrange
    account1 = create_test_account()
    account2 = create_test_account()
    user1 = create_test_user(
        account=account1,
        is_account_owner=False,
    )
    user2 = create_test_user(account=account2, email='test@tsst.com')
    group = create_test_group(account2, users=[user2])
    workflow = create_test_workflow(user1)
    event = WorkflowEventService.comment_created_event(
        text='Comment 1',
        task=workflow.tasks.get(number=1),
        user=user1,
        after_create_actions=False,
    )
    api_client.token_authenticate(user1)

    # act
    response = api_client.get(
        '/reports/highlights',
        data={
            'current_performer_group_ids': group.id,
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['text'] == event.text


def test_highlights__current_performer_group_ids_with_users__ok(api_client):
    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    first_invited = create_invited_user(user)
    group = create_test_group(
        account=account,
        users=[first_invited],
    )
    workflow_1 = create_test_workflow(user)
    workflow_2 = create_test_workflow(user)

    event_1 = WorkflowEventService.comment_created_event(
        text='Comment 1',
        task=workflow_1.tasks.get(number=1),
        user=user,
        after_create_actions=False,
    )
    event_2 = WorkflowEventService.comment_created_event(
        text='Comment 2',
        task=workflow_2.tasks.get(number=1),
        user=first_invited,
        after_create_actions=False,
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/reports/highlights',
        data={
            'current_performer_group_ids': group.id,
            'current_performer_ids': user.id,
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['text'] == event_2.text
    assert response.data[1]['text'] == event_1.text


def test__force_delay_workflow_event__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    delay = Delay.objects.create(
        task=task,
        start_date=timezone.now(),
        duration=timedelta(days=1, minutes=1, seconds=1),
        workflow=workflow,
    )

    event = WorkflowEventService.force_delay_workflow_event(
        workflow=workflow,
        delay=delay,
        user=user,
        after_create_actions=False,
    )

    # act
    response = api_client.get('/reports/highlights')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data = response.data[0]
    assert data['id'] == event.id
    assert data['type'] == WorkflowEventType.FORCE_DELAY
    assert data['created_tsp'] == event.created.timestamp()
    assert data['user_id'] == user.id
    assert data['target_user_id'] is None
    assert data['workflow']['id'] == workflow.id
    assert data['delay']['id'] == delay.id
    assert data['delay']['duration'] == '1 00:01:01'
    assert data['delay']['start_date_tsp'] == delay.start_date.timestamp()
    assert data['delay']['end_date_tsp'] is None
    assert data['delay']['estimated_end_date_tsp'] == (
        delay.estimated_end_date.timestamp()
    )


def test__force_resume__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user, tasks_count=1)
    WorkflowEventService.force_resume_workflow_event(
        workflow=workflow,
        user=user,
        after_create_actions=False,
    )

    # act
    response = api_client.get('/reports/highlights')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data = response.data[0]
    assert data['type'] == WorkflowEventType.FORCE_RESUME
    assert data['created'] is not None
    assert data['user_id'] == user.id
    assert data['target_user_id'] is None
    assert data['workflow']['id'] == workflow.id


def test__kickoff_field_type_user__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    field_template = FieldTemplate.objects.create(
        name='User Field',
        order=1,
        type=FieldType.USER,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
    )
    api_client.token_authenticate(user)

    response = api_client.post(
        path=f'/templates/{template.id}/run',
        data={
            'name': 'Test name',
            'kickoff': {
                field_template.api_name: user.email,
            },
        },
    )
    workflow = Workflow.objects.get(id=response.data['id'])
    field = workflow.kickoff_instance.output.first()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/reports/highlights')

    # assert
    assert response.status_code == 200
    field_data = response.data[0]['workflow']['kickoff']['output'][0]
    assert field_data['type'] == field.type
    assert field_data['is_required'] == field.is_required
    assert field_data['name'] == field.name
    assert field_data['description'] == field.description
    assert field_data['api_name'] == field.api_name
    # TODO Replace in https://my.pneumatic.app/workflows/18137/
    assert field_data['value'] == user.get_full_name()
    assert field_data['selections'] == []
    assert field_data['attachments'] == []
    assert field_data['user_id'] == user.id


def test__due_date_changed__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    due_date = timezone.now() + timedelta(hours=1)
    task.due_date = due_date
    task.save(update_fields=['due_date'])
    event = WorkflowEventService.due_date_changed_event(
        task=task,
        user=user,
        after_create_actions=False,
    )

    # act
    response = api_client.get('/reports/highlights')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data = response.data[0]

    assert data['user_id'] == user.id
    assert data['type'] == WorkflowEventType.DUE_DATE_CHANGED
    assert data['created_tsp'] == event.created.timestamp()
    assert data['task']['id'] == task.id
    assert data['task']['name'] == task.name
    assert data['task']['number'] == task.number
    assert data['task']['description'] == task.description
    assert data['task']['performers'] == [
        {
            'source_id': user.id,
            'type': 'user',
            'is_completed': False,
            'date_completed_tsp': None,
        },
    ]
    assert data['task']['due_date_tsp'] == due_date.timestamp()
    assert data['workflow']['id'] == workflow.id
    assert data['workflow']['template']['id'] == workflow.template.id
    assert data['workflow']['template']['name'] == workflow.template.name


def test__delay_workflow_event__not_found(api_client):

    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True,
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user, tasks_count=2)
    task = workflow.tasks.get(number=1)
    delay = Delay.objects.create(
        task=task,
        start_date=timezone.now(),
        duration=timedelta(days=1, minutes=1, seconds=1),
        workflow=workflow,
    )

    WorkflowEventService.workflow_delay_event(
        workflow=workflow,
        delay=delay,
        after_create_actions=False,
    )

    # act
    response = api_client.get('/reports/highlights')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test__sub_workflow_run__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        name='Parent workflow',
        user=user,
        tasks_count=1,
    )
    ancestor_task = workflow.tasks.get(number=1)
    ancestor_task.name = 'Ancestor task name'
    ancestor_task.description = 'Ancestor task desc'
    ancestor_task.due_date = timezone.now() + timedelta(hours=1)
    ancestor_task.save()

    user_2 = create_test_user(
        email='test@test.test',
        is_account_owner=False,
        account=user.account,
    )
    sub_workflow = create_test_workflow(
        user=user_2,
        name='New sub workflow',
        ancestor_task=ancestor_task,
        is_urgent=True,
        due_date=timezone.now() + timedelta(days=30),
    )

    event = WorkflowEventService.sub_workflow_run_event(
        user=user,
        workflow=workflow,
        sub_workflow=sub_workflow,
        after_create_actions=False,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/reports/highlights')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data = response.data[0]

    assert data['user_id'] == user.id
    assert data['type'] == WorkflowEventType.SUB_WORKFLOW_RUN
    assert data['created_tsp'] == event.created.timestamp()

    task_data = data['task']
    assert task_data['id'] == ancestor_task.id
    assert task_data['name'] == ancestor_task.name
    assert task_data['number'] == ancestor_task.number
    assert task_data['description'] == ancestor_task.description
    assert task_data['performers'] == [
        {
            'source_id': user.id,
            'type': 'user',
            'is_completed': False,
            'date_completed_tsp': None,
        },
    ]
    assert task_data['due_date_tsp'] == ancestor_task.due_date.timestamp()

    assert task_data['sub_workflow']['id'] == sub_workflow.id
    assert task_data['sub_workflow']['name'] == sub_workflow.name
    assert task_data['sub_workflow']['description'] == (
        sub_workflow.description
    )
    assert task_data['sub_workflow']['date_created_tsp'] == (
        sub_workflow.date_created.timestamp()
    )
    assert task_data['sub_workflow']['due_date_tsp'] == (
        sub_workflow.due_date.timestamp()
    )
    assert task_data['sub_workflow']['is_urgent'] == (
        sub_workflow.is_urgent
    )

    assert data['workflow']['id'] == workflow.id
    assert data['workflow']['template']['id'] == workflow.template.id
    assert data['workflow']['template']['name'] == workflow.template.name
