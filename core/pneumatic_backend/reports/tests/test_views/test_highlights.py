import pytest
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from pneumatic_backend.processes.api_v2.services import (
    WorkflowEventService,
)
from pneumatic_backend.processes.models import (
    Delay,
    FieldTemplate,
    Workflow,
    WorkflowEvent,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_invited_user,
    create_test_workflow,
    create_test_account,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_template
)
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    WorkflowEventType,
    FieldType,
)
from pneumatic_backend.processes.api_v2.services.task.performers import (
    TaskPerformersService
)


UserModel = get_user_model()
datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def replica_mock(mocker):
    mocker.patch('django.conf.settings.REPLICA', 'default')
    yield


def test__ordering__ok(api_client):
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    workflow = create_test_workflow(user)
    task = workflow.tasks.order_by('number').first()
    task.is_completed = True
    task.date_completed = timezone.now()
    task.save()

    WorkflowEventService.task_complete_event(
        task=task,
        user=user
    )
    second_task = task.next
    second_task.date_started = timezone.now()
    task.save(update_fields=['date_started'])
    WorkflowEventService.comment_created_event(
        text='comment',
        workflow=workflow,
        user=user,
        after_create_actions=False
    )

    api_client.token_authenticate(user)
    response = api_client.get('/reports/highlights')

    assert response.status_code == 200

    assert len(response.data) == 1
    assert response.data[0]['type'] == WorkflowEventType.COMMENT


def test__return_task__ok(api_client):
    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    workflow = create_test_workflow(user)
    task = workflow.tasks.order_by('number').first()
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': task.id,
        }
    )
    api_client.post(
        f'/workflows/{workflow.id}/task-revert',
        data={},
    )

    # act
    response = api_client.get('/reports/highlights')

    # assert
    assert response.status_code == 200

    assert len(response.data) == 1
    event_data = response.data[0]
    assert event_data['type'] == WorkflowEventType.TASK_REVERT
    assert event_data['created'] is not None
    assert type(event_data['created_tsp']) is float


def test__return_to_task__ok(api_client):
    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    workflow = create_test_workflow(user)
    task = workflow.tasks.order_by('number').first()
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={
            'task_id': task.id,
        }
    )
    api_client.post(
        f'/workflows/{workflow.id}/return-to',
        data={'task': workflow.tasks.get(number=1).id},
    )

    # act
    response = api_client.get(
        f'/reports/highlights'
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
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )

    workflow = create_test_workflow(user)
    other_workflow = create_test_workflow(user)
    WorkflowEventService.workflow_run_event(other_workflow)
    task = workflow.tasks.order_by('number').first()
    task.is_completed = True
    task.date_completed = timezone.now()
    task.save()
    WorkflowEventService.task_complete_event(
        task=task,
        user=user
    )
    second_task = task.next
    second_task.date_started = timezone.now()
    task.save(update_fields=['date_started'])
    WorkflowEventService.comment_created_event(
        text='Revert',
        workflow=workflow,
        user=user,
        after_create_actions=False
    )
    api_client.token_authenticate(user)

    response = api_client.get(f'/reports/highlights')

    assert response.status_code == 200

    assert len(response.data) == 2
    assert response.data[0]['type'] == WorkflowEventType.COMMENT
    assert response.data[1]['type'] == WorkflowEventType.RUN
    assert response.data[1]['workflow']['is_external'] is False


def test_highlights_date_range(api_client):
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )

    workflow = create_test_workflow(user)
    WorkflowEventService.workflow_run_event(workflow)
    task = workflow.tasks.order_by('number').first()
    WorkflowEventService.task_started_event(task)
    task.is_completed = True
    task.date_completed = timezone.now()
    task.save()

    WorkflowEventService.task_complete_event(task=task, user=user)
    second_task = task.next
    WorkflowEventService.task_started_event(second_task)
    second_task.date_started = timezone.now() - timedelta(days=2)
    second_task.save(update_fields=['date_started'])
    WorkflowEventService.comment_created_event(
        text='Revert',
        workflow=workflow,
        user=user,
        after_create_actions=False
    )
    workflow_new = create_test_workflow(user)
    task = workflow_new.tasks.order_by('number').first()
    WorkflowEventService.task_started_event(task)
    task.is_completed = True
    task.date_completed = timezone.now()
    task.save()
    event = WorkflowEvent.objects.get(
        type=WorkflowEventType.TASK_START,
        task_json__id=task.id
    )
    event.created = timezone.now() - timedelta(days=2)
    event.save()
    WorkflowEventService.task_complete_event(
        task=task,
        user=user
    )

    date_after = event.created.isoformat()
    date_before = (
        timezone.now() + timedelta(days=1)
    ).isoformat()
    api_client.token_authenticate(user)

    response = api_client.get(
        '/reports/highlights',
        data={
            'date_after': date_after,
            'date_before': date_before,
        }
    )

    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['type'] == WorkflowEventType.TASK_COMPLETE
    assert response.data[1]['type'] == WorkflowEventType.COMMENT


def test_highlights__used_tsp__ok(api_client):
    user = create_test_user()
    workflow = create_test_workflow(user)
    WorkflowEventService.workflow_run_event(workflow)
    task = workflow.tasks.order_by('number').first()
    WorkflowEventService.task_started_event(task)
    task.is_completed = True
    task.date_completed = timezone.now() + timedelta(hours=11)
    task.save()

    WorkflowEventService.task_complete_event(task=task, user=user)

    second_task = task.next
    WorkflowEventService.task_started_event(second_task)
    second_task.date_started = timezone.now() + timedelta(hours=10)
    second_task.save(update_fields=['date_started'])
    WorkflowEventService.comment_created_event(
        text='Revert',
        workflow=workflow,
        user=user,
        after_create_actions=False
    )

    workflow_new = create_test_workflow(user)
    task = workflow_new.tasks.order_by('number').first()
    WorkflowEventService.task_started_event(task)
    task.is_completed = True
    task.date_completed = timezone.now() + timedelta(hours=7)
    task.save()

    event = WorkflowEvent.objects.get(
        type=WorkflowEventType.TASK_START,
        task_json__id=task.id
    )
    event.created = timezone.now() + timedelta(hours=7)
    event.save()
    WorkflowEventService.task_complete_event(
        task=task,
        user=user
    )

    date_after = timezone.now() - timedelta(hours=1)
    date_before = timezone.now() + timedelta(hours=1)
    api_client.token_authenticate(user)

    response = api_client.get(
        '/reports/highlights',
        data={
            'date_after_tsp': date_after.timestamp(),
            'date_before_tsp': date_before.timestamp(),
        }
    )

    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['type'] == WorkflowEventType.TASK_COMPLETE
    assert response.data[1]['type'] == WorkflowEventType.COMMENT


def test_highlights_by_template(api_client):
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    workflow_1 = create_test_workflow(user)
    workflow_2 = create_test_workflow(user)
    workflow_3 = create_test_workflow(user)

    WorkflowEventService.comment_created_event(
        user=user,
        text='Comment 1',
        workflow=workflow_1,
        after_create_actions=False
    )
    event_2 = WorkflowEventService.comment_created_event(
        user=user,
        text='Comment 2',
        workflow=workflow_2,
        after_create_actions=False
    )
    event_3 = WorkflowEventService.comment_created_event(
        user=user,
        text='Comment 3',
        workflow=workflow_3,
        after_create_actions=False
    )

    api_client.token_authenticate(user)

    response = api_client.get(
        f'/reports/highlights?templates={workflow_2.template.id},'
        f'{workflow_3.template.id}'
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
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )

    workflow_1 = create_test_workflow(user)
    workflow_2 = create_test_workflow(user)
    workflow_3 = create_test_workflow(user)

    WorkflowEventService.comment_created_event(
        text='Comment 1',
        workflow=workflow_1,
        user=user,
        after_create_actions=False
    )
    event_2 = WorkflowEventService.comment_created_event(
        text='Comment 2',
        workflow=workflow_2,
        user=user,
        after_create_actions=False
    )
    WorkflowEventService.comment_created_event(
        text='Revert',
        workflow=workflow_3,
        user=user,
        after_create_actions=False
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


def test_highlights_by_users(api_client):
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    first_invited = create_invited_user(user)
    second_invited = create_invited_user(user, 'test_n@pneumatic.app')

    workflow_1 = create_test_workflow(user)
    workflow_2 = create_test_workflow(user)
    workflow_3 = create_test_workflow(user)

    WorkflowEventService.comment_created_event(
        text='Comment 1',
        workflow=workflow_1,
        user=user,
        after_create_actions=False
    )
    event_2 = WorkflowEventService.comment_created_event(
        text='Comment 2',
        workflow=workflow_2,
        user=first_invited,
        after_create_actions=False
    )
    event_3 = WorkflowEventService.comment_created_event(
        text='Comment 3',
        workflow=workflow_3,
        user=second_invited,
        after_create_actions=False
    )

    api_client.token_authenticate(user)

    response = api_client.get(
        f'/reports/highlights?users={first_invited.id},{second_invited.id}'
    )

    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['text'] == event_3.text
    assert response.data[1]['text'] == event_2.text


def test_highlights_complete_workflow(api_client):
    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    workflow = create_test_workflow(user)
    WorkflowEventService.workflow_run_event(workflow)
    for task in workflow.tasks.order_by('number'):
        task.is_completed = True
        task.date_completed = timezone.now()
        task.taskperformer_set.update(is_completed=True)
        task.save(update_fields=['is_completed', 'date_completed'])
        next_task = task.next
        if next_task:
            next_task.date_started = timezone.now()
            next_task.save(update_fields=['date_started'])
        WorkflowEventService.task_complete_event(
            task=task,
            user=user
        )
    workflow.status = WorkflowStatus.DONE
    workflow.save(update_fields=['status'])
    WorkflowEventService.workflow_complete_event(
        workflow=workflow,
        user=user,
    )

    api_client.token_authenticate(user)
    response = api_client.get('/reports/highlights')

    assert response.status_code == 200
    assert response.data[0]['type'] == (
        WorkflowEventType.COMPLETE
    )


def test__is_urgent_event__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user)
    WorkflowEventService.workflow_urgent_event(
        event_type=WorkflowEventType.URGENT,
        workflow=workflow,
        user=user
    )
    event = WorkflowEventService.workflow_urgent_event(
        event_type=WorkflowEventType.NOT_URGENT,
        workflow=workflow,
        user=user
    )

    # act
    response = api_client.get('/reports/highlights')

    # assert
    assert response.status_code == 200
    event_data = response.data[0]
    assert event_data['id'] == event.id
    assert event_data['created'] == event.created.strftime(datetime_format)
    assert event_data['created_tsp'] == event.created.timestamp()
    assert event_data['type'] == WorkflowEventType.NOT_URGENT


def test__is_not_urgent_event__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user)
    WorkflowEventService.workflow_urgent_event(
        event_type=WorkflowEventType.NOT_URGENT,
        workflow=workflow,
        user=user
    )
    event = WorkflowEventService.workflow_urgent_event(
        event_type=WorkflowEventType.URGENT,
        workflow=workflow,
        user=user
    )

    # act
    response = api_client.get('/reports/highlights')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    event_data = response.data[0]
    assert event_data['id'] == event.id
    assert event_data['created'] == event.created.strftime(datetime_format)
    assert event_data['created_tsp'] == event.created.timestamp()
    assert event_data['type'] == WorkflowEventType.URGENT


def test__performer_created_event__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    user_performer = create_test_user(
        email='t@t.t',
        account=user.account
    )
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    TaskPerformersService.create_performer(
        user_key=user_performer.id,
        request_user=user,
        task=task,
        run_actions=False,
        current_url='/page',
        is_superuser=False
    )
    WorkflowEventService.performer_created_event(
        task=task,
        user=user,
        performer=user_performer
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
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    user_performer = create_test_user(
        email='t@t.t',
        account=user.account
    )
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    WorkflowEventService.performer_deleted_event(
        user=user,
        task=task,
        performer=user_performer
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


def test__force_delay_workflow_event__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    delay = Delay.objects.create(
        task=task,
        start_date=timezone.now(),
        duration=timedelta(days=1, minutes=1, seconds=1)
    )

    event = WorkflowEventService.force_delay_workflow_event(
        workflow=workflow,
        delay=delay,
        user=user
    )

    # act
    response = api_client.get('/reports/highlights')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data = response.data[0]
    assert data['id'] == event.id
    assert data['type'] == WorkflowEventType.FORCE_DELAY
    assert data['created'] == event.created.strftime(datetime_format)
    assert data['created_tsp'] == event.created.timestamp()
    assert data['user_id'] == user.id
    assert data['target_user_id'] is None
    assert data['workflow']['id'] == workflow.id
    assert data['delay']['id'] == delay.id
    assert data['delay']['duration'] == '1 00:01:01'
    assert data['delay']['start_date'] == (
        delay.start_date.strftime(datetime_format)
    )
    assert data['delay']['start_date_tsp'] == delay.start_date.timestamp()
    assert data['delay']['end_date'] is None
    assert data['delay']['estimated_end_date'] == (
        delay.estimated_end_date.strftime(datetime_format)
    )
    assert data['delay']['estimated_end_date_tsp'] == (
        delay.estimated_end_date.timestamp()
    )


def test__force_resume__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_user(
        email='owner@test.test',
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user, tasks_count=1)
    WorkflowEventService.force_resume_workflow_event(
        workflow=workflow,
        user=user
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
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1
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
                field_template.api_name: user.id
            }
        }
    )
    workflow = Workflow.objects.get(id=response.data['workflow_id'])
    field = workflow.kickoff_instance.output.first()
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/reports/highlights')

    # assert
    assert response.status_code == 200
    field_data = response.data[0]['workflow']['kickoff']['output'][0]
    assert field_data['type'] == field.type
    assert field_data['is_required'] == field.is_required
    assert field_data['name'] == field.name
    assert field_data['description'] == field.description
    assert field_data['api_name'] == field.api_name
    # TODO Replace in https://my.pneumatic.app/workflows/18137/
    assert field_data['value'] == str(user.id)  # user.get_full_name()
    assert field_data['selections'] == []
    assert field_data['attachments'] == []
    assert field_data['user_id'] == user.id


def test__due_date_changed__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    due_date = timezone.now() + timedelta(hours=1)
    task.due_date = due_date
    task.save(update_fields=['due_date'])
    event = WorkflowEventService.due_date_changed_event(
        task=task,
        user=user
    )

    # act
    response = api_client.get('/reports/highlights')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data = response.data[0]

    assert data['user_id'] == user.id
    assert data['type'] == WorkflowEventType.DUE_DATE_CHANGED
    assert data['created'] == event.created.strftime(datetime_format)
    assert data['created_tsp'] == event.created.timestamp()
    assert data['task']['id'] == task.id
    assert data['task']['name'] == task.name
    assert data['task']['number'] == task.number
    assert data['task']['description'] == task.description
    assert data['task']['performers'] == [user.id]
    str_due_date = due_date.strftime(datetime_format)
    assert data['task']['due_date'] == str_due_date
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
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        is_account_owner=False
    )
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user, tasks_count=2)
    task = workflow.current_task_instance
    delay = Delay.objects.create(
        task=task,
        start_date=timezone.now(),
        duration=timedelta(days=1, minutes=1, seconds=1)
    )

    WorkflowEventService.workflow_delay_event(
        workflow=workflow,
        delay=delay
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
        tasks_count=1
    )
    ancestor_task = workflow.current_task_instance
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
        due_date=timezone.now() + timedelta(days=30)
    )

    event = WorkflowEventService.sub_workflow_run_event(
        user=user,
        workflow=workflow,
        sub_workflow=sub_workflow
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
    assert data['created'] == event.created.strftime(datetime_format)
    assert data['created_tsp'] == event.created.timestamp()

    task_data = data['task']
    assert task_data['id'] == ancestor_task.id
    assert task_data['name'] == ancestor_task.name
    assert task_data['number'] == ancestor_task.number
    assert task_data['description'] == ancestor_task.description
    assert task_data['performers'] == [user.id]
    assert task_data['due_date'] == (
        ancestor_task.due_date.strftime(datetime_format)
    )
    assert task_data['due_date_tsp'] == ancestor_task.due_date.timestamp()

    assert task_data['sub_workflow']['id'] == sub_workflow.id
    assert task_data['sub_workflow']['name'] == sub_workflow.name
    assert task_data['sub_workflow']['description'] == (
        sub_workflow.description
    )
    assert task_data['sub_workflow']['date_created'] == (
        sub_workflow.date_created.strftime(datetime_format)
    )
    assert task_data['sub_workflow']['date_created_tsp'] == (
        sub_workflow.date_created.timestamp()
    )
    assert task_data['sub_workflow']['due_date'] == (
        sub_workflow.due_date.strftime(datetime_format)
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
