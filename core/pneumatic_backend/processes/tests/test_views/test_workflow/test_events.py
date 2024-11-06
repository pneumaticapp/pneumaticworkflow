import pytest
from datetime import timedelta
from django.utils import timezone
from pneumatic_backend.processes.api_v2.services import (
    WorkflowEventService,
)
from pneumatic_backend.processes.models import (
    Workflow,
    Delay,
    FileAttachment,
    TaskPerformer,
    FieldTemplate,
    FieldTemplateSelection,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_workflow,
    create_test_account,
    create_test_guest
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    DirectlyStatus,
    FieldType,
    WorkflowEventType,
    CommentStatus,
)
from pneumatic_backend.processes.api_v2.services.task.performers import (
    TaskPerformersService
)
from pneumatic_backend.authentication.services import GuestJWTAuthService

pytestmark = pytest.mark.django_db
datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'


def test_events__ordering_date__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.order_by('number').first()
    WorkflowEventService.task_started_event(task)
    task.is_completed = True
    task.date_completed = timezone.now()
    task.save()

    WorkflowEventService.task_complete_event(
        task=task,
        user=user
    )
    sec_task = task.next
    WorkflowEventService.task_started_event(sec_task)
    sec_task.date_started = timezone.now()
    sec_task.save(update_fields=['date_started'])
    WorkflowEventService.task_revert_event(
        task=workflow.current_task_instance,
        user=user
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/workflows/{workflow.id}/events?ordering=created'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 4
    assert response.data[0]['type'] == WorkflowEventType.TASK_START
    assert response.data[1]['type'] == WorkflowEventType.TASK_COMPLETE


def test_events__ordering_date_inverted__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.order_by('number').first()
    WorkflowEventService.task_started_event(task)
    task.is_completed = True
    task.date_completed = timezone.now()
    task.save()

    WorkflowEventService.task_complete_event(task=task, user=user)
    sec_task = task.next
    sec_task.date_started = timezone.now()
    sec_task.save(update_fields=['date_started'])
    WorkflowEventService.task_started_event(sec_task)
    WorkflowEventService.comment_created_event(
        workflow=workflow,
        user=user,
        text='Test',
        after_create_actions=False
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/workflows/{workflow.id}/events?ordering=-created'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 4
    assert response.data[0]['type'] == WorkflowEventType.COMMENT
    assert response.data[1]['type'] == WorkflowEventType.TASK_START


def test_events__include_comments_false__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.order_by('number').first()
    WorkflowEventService.task_started_event(task)
    task.is_completed = True
    task.date_completed = timezone.now()
    task.save()

    WorkflowEventService.task_complete_event(
        task=task,
        user=user
    )
    sec_task = task.next
    WorkflowEventService.task_skip_event(sec_task)
    sec_task.date_started = timezone.now()
    sec_task.save(update_fields=['date_started'])
    WorkflowEventService.comment_created_event(
        text='No attachments',
        workflow=workflow,
        user=user,
        after_create_actions=False
    )
    api_client.token_authenticate(user)

    response = api_client.get(
        f'/workflows/{workflow.id}/events?include_comments=false'
    )

    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]['type'] == WorkflowEventType.TASK_SKIP
    assert response.data[1]['type'] == WorkflowEventType.TASK_COMPLETE
    assert response.data[2]['type'] == WorkflowEventType.TASK_START


def test_events__only_attachments_true__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    WorkflowEventService.task_started_event(workflow.current_task_instance)

    attachment = FileAttachment.objects.create(
        name='filename.png',
        url='https://path.to.file/filename.png',
        size=141352,
        account_id=user.account_id,
    )
    event = WorkflowEventService.comment_created_event(
        text='No attachments',
        workflow=workflow,
        user=user,
        attachments=[attachment.id],
        after_create_actions=False
    )
    attachment.event = event
    attachment.save()
    WorkflowEventService.comment_created_event(
        text='There is no attachments here',
        workflow=workflow,
        user=user,
        after_create_actions=False
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/workflows/{workflow.id}/events?only_attachments=true'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == event.id
    assert response.data[0]['text'] == event.text
    assert response.data[0]['type'] == WorkflowEventType.COMMENT


def test_events__not_admin_user__ok(api_client):

    # arrange
    owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        account=owner.account,
        is_account_owner=False,
        is_admin=False,
        email='no@admin.com'
    )
    workflow = create_test_workflow(owner)

    task = workflow.current_task_instance
    WorkflowEventService.task_started_event(task)
    task.is_completed = True
    task.date_completed = timezone.now()
    task.save()

    WorkflowEventService.task_complete_event(task=task, user=user)
    task_2 = task.next
    WorkflowEventService.task_started_event(task_2)
    task_2.date_started = timezone.now()
    task_2.save(update_fields=['date_started'])
    WorkflowEventService.comment_created_event(
        text='No attachments',
        workflow=workflow,
        user=user,
        after_create_actions=False
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 4
    assert response.data[0]['type'] == WorkflowEventType.COMMENT
    assert response.data[1]['type'] == WorkflowEventType.TASK_START
    assert response.data[2]['type'] == WorkflowEventType.TASK_COMPLETE
    assert response.data[3]['type'] == WorkflowEventType.TASK_START


def test_events__guest__ok(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
    )
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)

    TaskPerformer.objects.by_task(
        task_1.id
    ).by_user(
        account_owner.id
    ).update(directly_status=DirectlyStatus.DELETED)

    TaskPerformer.objects.create(
        task_id=task_1.id,
        user_id=guest.id
    )

    str_token = GuestJWTAuthService.get_str_token(
        task_id=task_1.id,
        user_id=guest.id,
        account_id=account.id
    )

    WorkflowEventService.task_started_event(task_1)
    WorkflowEventService.comment_created_event(
        text='Comment 1',
        workflow=workflow,
        user=account_owner,
        after_create_actions=False
    )
    workflow.current_task = 2
    workflow.save()
    workflow.refresh_from_db()
    WorkflowEventService.comment_created_event(
        text='Comment 2',
        workflow=workflow,
        user=account_owner,
        after_create_actions=False
    )

    # act
    response = api_client.get(
        f'/workflows/{workflow.id}/events',
        **{'X-Guest-Authorization': str_token}
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['type'] == WorkflowEventType.COMMENT
    event_performers = response.data[0]['task']['performers']
    assert len(event_performers) == 1
    assert event_performers[0] == guest.id


def test_events__guest_another_workflow__permission_denied(api_client):

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
        f'/workflows/{workflow_1.id}/events',
        **{'X-Guest-Authorization': str_token_2}
    )

    # assert
    assert response.status_code == 403


def test_retrieve__external_workflow__ok(
    mocker,
    api_client,
    session_mock,
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        is_public=True,
    )
    token = f'Token {template.public_id}'
    mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.public_api_request'
    )

    # act
    run_response = api_client.post(
        path=f'/templates/public/run',
        data={
            'captcha': 'skip'
        },
        **{'X-Public-Authorization': token}
    )

    workflow = Workflow.objects.get(template=template)
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert run_response.status_code == 200
    assert response.status_code == 200
    assert len(response.data) == 1
    response_data = response.data[0]
    assert response_data['type'] == WorkflowEventType.TASK_START
    assert response_data['user_id'] is None
    assert response_data['task']['id'] == workflow.current_task_instance.id


def test_retrieve__paginated__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user)

    WorkflowEventService.comment_created_event(
        text='Comment 1',
        workflow=workflow,
        user=user,
        after_create_actions=False
    )
    WorkflowEventService.comment_created_event(
        text='Comment 2',
        workflow=workflow,
        user=user,
        after_create_actions=False
    )
    response = api_client.get(
        path=f'/workflows/{workflow.id}/events?limit=1&offset=1'
    )

    # assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['count'] == 2
    assert response_data['next'] is None
    assert response_data['previous'] is not None
    assert len(response_data['results']) == 1


def test_retrieve__workflow_started__not_found(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    WorkflowEventService.workflow_run_event(workflow)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_retrieve__task_started__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    current_task = workflow.current_task_instance

    due_date = timezone.now() + timedelta(days=1)
    current_task.due_date = due_date
    current_task.save()
    event = WorkflowEventService.task_started_event(current_task)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    event_data = response.data[0]
    assert event_data['id'] == event.id
    assert event_data['created'] == event.created.strftime(datetime_format)
    assert event_data['created_tsp'] == event.created.timestamp()
    assert event_data['type'] == WorkflowEventType.TASK_START
    assert event_data['workflow_id'] == workflow.id

    task_data = response.data[0]['task']
    assert task_data['id'] == current_task.id
    assert task_data['description'] == current_task.description
    assert task_data['name'] == current_task.name
    assert task_data['number'] == current_task.number
    assert len(task_data['performers']) == 1
    assert task_data['performers'] == [user.id]
    assert task_data['due_date'] == due_date.strftime(datetime_format)
    assert task_data['due_date_tsp'] == due_date.timestamp()


def test_retrieve__not_urgent_workflow__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user)
    event = WorkflowEventService.workflow_urgent_event(
        event_type=WorkflowEventType.NOT_URGENT,
        workflow=workflow,
        user=user
    )

    # act
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    event_data = response.data[0]
    assert event_data['id'] == event.id
    assert event_data['created'] == event.created.strftime(datetime_format)
    assert event_data['created_tsp'] == event.created.timestamp()
    assert event_data['type'] == WorkflowEventType.NOT_URGENT
    assert event_data['workflow_id'] == workflow.id


def test_retrieve__urgent_workflow__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user)
    event = WorkflowEventService.workflow_urgent_event(
        event_type=WorkflowEventType.URGENT,
        workflow=workflow,
        user=user,
    )

    # act
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    event_data = response.data[0]
    assert event_data['id'] == event.id
    assert event_data['created'] == event.created.strftime(datetime_format)
    assert event_data['created_tsp'] == event.created.timestamp()
    assert event_data['type'] == WorkflowEventType.URGENT
    assert event_data['workflow_id'] == workflow.id


def test_retrieve__performer_created__ok(api_client):

    # arrange
    user = create_test_user()
    user_performer = create_test_user(
        email='t@t.t',
        account=user.account
    )
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.current_task_instance
    TaskPerformersService.create_performer(
        task=task,
        request_user=user,
        user_key=user_performer.id,
        run_actions=False,
        current_url='/page',
        is_superuser=False
    )
    event = WorkflowEventService.performer_created_event(
        user=user,
        task=task,
        performer=user_performer
    )

    # act
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    event_data = response.data[0]
    assert event_data['id'] == event.id
    assert event_data['created'] == event.created.strftime(datetime_format)
    assert event_data['created_tsp'] == event.created.timestamp()
    assert event_data['user_id'] == user.id
    assert event_data['target_user_id'] == user_performer.id
    assert event_data['workflow_id'] == workflow.id
    assert event_data['type'] == (
        WorkflowEventType.TASK_PERFORMER_CREATED
    )
    task_data = response.data[0]['task']
    assert task_data['id'] == task.id
    assert task_data['description'] == task.description
    assert task_data['name'] == task.name
    assert task_data['number'] == task.number
    assert task_data['due_date'] is None
    assert len(task_data['performers']) == 2
    assert len(task_data['performers'])
    assert user.id in task_data['performers']
    assert user_performer.id in task_data['performers']


def test_retrieve__performer_deleted__ok(api_client):

    # arrange
    user = create_test_user()
    user_performer = create_test_user(
        email='t@t.t',
        account=user.account
    )
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.current_task_instance
    TaskPerformersService.create_performer(
        task=task,
        request_user=user,
        user_key=user_performer.id,
        run_actions=False,
        current_url='/page',
        is_superuser=False
    )
    TaskPerformersService.delete_performer(
        task=task,
        request_user=user,
        user_key=user_performer.id,
        run_actions=False
    )
    event = WorkflowEventService.performer_deleted_event(
        user=user,
        task=task,
        performer=user_performer
    )

    # act
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    event_data = response.data[0]
    assert event_data['id'] == event.id
    assert event_data['created'] == event.created.strftime(datetime_format)
    assert event_data['created_tsp'] == event.created.timestamp()
    assert event_data['workflow_id'] == workflow.id
    assert event_data['user_id'] == user.id
    assert event_data['target_user_id'] == user_performer.id
    assert event_data['type'] == (
        WorkflowEventType.TASK_PERFORMER_DELETED
    )
    task_data = response.data[0]['task']
    assert task_data['id'] == task.id
    assert task_data['description'] == task.description
    assert task_data['name'] == task.name
    assert task_data['number'] == task.number
    assert task_data['due_date'] is None
    assert len(task_data['performers']) == 1
    assert len(task_data['performers'])
    assert user.id in task_data['performers']


def test_retrieve__workflow_delay_event__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.current_task_instance
    delay = Delay.objects.create(
        task=task,
        start_date=timezone.now(),
        duration=timedelta(days=1)
    )
    event = WorkflowEventService.workflow_delay_event(
        workflow=workflow,
        delay=delay
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/workflows/{workflow.id}/events',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    event_data = response.data[0]
    assert event_data['id'] == event.id
    assert event_data['created'] == event.created.strftime(datetime_format)
    assert event_data['created_tsp'] == event.created.timestamp()
    assert event_data['type'] == WorkflowEventType.DELAY
    assert event_data['workflow_id'] == workflow.id

    delay_data = event_data['delay']
    assert delay_data['duration'] == '1 00:00:00'
    assert delay_data['end_date'] is None
    assert delay_data['start_date'] == (
        delay.start_date.strftime(datetime_format)
    )
    assert delay_data['start_date_tsp'] == delay.start_date.timestamp()
    assert delay_data['estimated_end_date'] == (
        delay.estimated_end_date.strftime(datetime_format)
    )
    assert delay_data['estimated_end_date_tsp'] == (
        delay.estimated_end_date.timestamp()
    )


def test_retrieve__force_delay_workflow_event__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.current_task_instance
    delay = Delay.objects.create(
        task=task,
        start_date=timezone.now(),
        duration=timedelta(days=1)
    )
    event = WorkflowEventService.force_delay_workflow_event(
        workflow=workflow,
        user=user,
        delay=delay,
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/workflows/{workflow.id}/events',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    event_data = response.data[0]
    assert event_data['id'] == event.id
    assert event_data['created'] == event.created.strftime(datetime_format)
    assert event_data['created_tsp'] == event.created.timestamp()
    assert event_data['type'] == WorkflowEventType.FORCE_DELAY
    assert event_data['workflow_id'] == workflow.id
    assert event_data['user_id'] == user.id

    delay_data = event_data['delay']
    assert delay_data['duration'] == '1 00:00:00'
    assert delay_data['end_date'] is None
    assert delay_data['start_date'] == (
        delay.start_date.strftime(datetime_format)
    )
    assert delay_data['start_date_tsp'] == delay.start_date.timestamp()
    assert delay_data['estimated_end_date'] == (
        delay.estimated_end_date.strftime(datetime_format)
    )
    assert delay_data['estimated_end_date_tsp'] == (
        delay.estimated_end_date.timestamp()
    )


def test_retrieve__force_resume_workflow_event__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    event = WorkflowEventService.force_resume_workflow_event(
        workflow=workflow,
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/workflows/{workflow.id}/events',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    event_data = response.data[0]
    assert event_data['id'] == event.id
    assert event_data['created'] == event.created.strftime(datetime_format)
    assert event_data['created_tsp'] == event.created.timestamp()
    assert event_data['type'] == WorkflowEventType.FORCE_RESUME
    assert event_data['workflow_id'] == workflow.id
    assert event_data['user_id'] == user.id


def test_retrieve__complete_task__field_user__ok(api_client):

    # arrange
    user = create_test_user()
    create_test_user(email='t@n.t', account=user.account)
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1
    )
    template_task = template.tasks.first()
    FieldTemplate.objects.create(
        name='User Field',
        order=1,
        type=FieldType.USER,
        is_required=True,
        task=template_task,
        template=template,
    )
    workflow = create_test_workflow(template=template, user=user)
    task = workflow.current_task_instance

    field = task.output.first()
    field.value = user.get_full_name()
    field.user_id = user.id
    field.save(update_fields=['value', 'user_id'])
    event = WorkflowEventService.task_complete_event(task=task, user=user)

    # act
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    event_data = response.data[0]
    assert event_data['id'] == event.id
    assert event_data['created'] == event.created.strftime(datetime_format)
    assert event_data['created_tsp'] == event.created.timestamp()
    assert event_data['type'] == WorkflowEventType.TASK_COMPLETE
    assert event_data['workflow_id'] == workflow.id
    assert event_data['user_id'] == user.id

    task_data = event_data['task']
    assert task_data['id'] == task.id
    assert task_data['description'] == task.description
    assert task_data['name'] == task.name
    assert task_data['number'] == task.number
    assert task_data['due_date'] is None
    assert task_data['performers'] == [user.id]

    assert len(task_data['output']) == 1
    field_data = task_data['output'][0]
    assert field_data['id'] == field.id
    assert field_data['type'] == field.type
    assert field_data['is_required'] == field.is_required
    assert field_data['name'] == field.name
    assert field_data['description'] == field.description
    assert field_data['api_name'] == field.api_name
    # TODO Replace in https://my.pneumatic.app/workflows/18137/
    assert field_data['value'] == str(user.id)  # user.get_full_name()
    assert field_data['selections'] == []
    assert field_data['attachments'] == []
    assert field_data['order'] == field.order
    assert field_data['user_id'] == user.id


def test_retrieve__complete_task__field_with_selections__ok(
    api_client
):

    # arrange
    user = create_test_user()
    user2 = create_test_user(email='t@n.t', account=user.account)
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1
    )
    template_task = template.tasks.first()
    template_task.add_raw_performer(
        performer_type=PerformerType.WORKFLOW_STARTER
    )
    template_task.add_raw_performer(user2)
    field_template = FieldTemplate.objects.create(
        name='Selection Field',
        order=1,
        type=FieldType.CHECKBOX,
        is_required=True,
        task=template_task,
        template=template,
    )
    FieldTemplateSelection.objects.create(
        field_template=field_template,
        template=template,
        value='some value',
    )

    workflow = create_test_workflow(user=user, template=template)
    task = workflow.current_task_instance
    field = task.output.first()
    field.value = 'some value'
    field.save(update_fields=['value'])
    selection = field.selections.first()
    selection.is_selected = True
    selection.save(update_fields=['is_selected'])
    WorkflowEventService.task_complete_event(task=task, user=user)

    # act
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert len(response.data[0]['task']['output']) == 1
    field_data = response.data[0]['task']['output'][0]
    assert field_data['id'] == field.id
    assert field_data['type'] == field.type
    assert field_data['is_required'] == field.is_required
    assert field_data['name'] == field.name
    assert field_data['description'] == field.description
    assert field_data['api_name'] == field.api_name
    assert field_data['value'] == selection.value
    assert field_data['attachments'] == []
    assert field_data['order'] == field.order
    assert field_data['user_id'] is None
    selection_data = field_data['selections'][0]
    assert selection_data['id'] == selection.id
    assert selection_data['api_name'] == selection.api_name
    assert selection_data['is_selected'] is True
    assert selection_data['value'] == selection.value


def test_retrieve__complete_task__field_with_attachments__ok(
    api_client
):

    # arrange
    user = create_test_user()
    user2 = create_test_user(email='t@n.t', account=user.account)
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1
    )
    template_task = template.tasks.first()
    template_task.add_raw_performer(
        performer_type=PerformerType.WORKFLOW_STARTER
    )
    template_task.add_raw_performer(user2)
    template_task.save()
    FieldTemplate.objects.create(
        name='File Field',
        order=1,
        type=FieldType.FILE,
        is_required=True,
        task=template_task,
        template=template,
    )

    workflow = create_test_workflow(user=user, template=template)
    task = workflow.current_task_instance
    field = task.output.first()
    attachment = FileAttachment.objects.create(
        name='john.cena',
        url='https://john.cena/john.cena',
        size=1488,
        account_id=user.account_id,
        output=field
    )
    field.value = attachment.url
    field.save(update_fields=['value'])

    WorkflowEventService.task_complete_event(task=task, user=user)

    # act
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert len(response.data[0]['task']['output']) == 1
    field_data = response.data[0]['task']['output'][0]
    assert field_data['id'] == field.id
    assert field_data['type'] == field.type
    assert field_data['is_required'] == field.is_required
    assert field_data['name'] == field.name
    assert field_data['description'] == field.description
    assert field_data['api_name'] == field.api_name
    assert field_data['value'] == attachment.url
    assert field_data['selections'] == []
    assert field_data['order'] == field.order
    assert field_data['user_id'] is None
    attachment_data = field_data['attachments'][0]
    assert attachment_data['id'] == attachment.id
    assert attachment_data['name'] == attachment.name
    assert attachment_data['url'] == attachment.url


def test_retrieve__task__due_date_changed__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.current_task_instance
    due_date = timezone.now() + timedelta(hours=1)
    task.due_date = due_date
    task.save(update_fields=['due_date'])
    event = WorkflowEventService.due_date_changed_event(
        task=task,
        user=user,
    )

    # act
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    event_data = response.data[0]
    assert event_data['id'] == event.id
    assert event_data['created'] == event.created.strftime(datetime_format)
    assert event_data['created_tsp'] == event.created.timestamp()
    assert event_data['workflow_id'] == workflow.id
    assert event_data['user_id'] == user.id
    assert event_data['type'] == WorkflowEventType.DUE_DATE_CHANGED

    task_data = event_data['task']
    assert task_data['id'] == task.id
    assert task_data['name'] == task.name
    assert task_data['number'] == task.number
    assert task_data['description'] == task.description
    assert task_data['due_date'] == due_date.strftime(datetime_format)
    assert task_data['due_date_tsp'] == due_date.timestamp()


def test_retrieve__comment__updated__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    text = 'Some comment'
    event = WorkflowEventService.comment_created_event(
        workflow=workflow,
        user=user,
        text=text,
        after_create_actions=False
    )
    event.updated = timezone.now() + timedelta(minutes=1)
    event.save()

    # act
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data = response.data[0]
    assert data['id'] == event.id
    assert data['created'] == event.created.strftime(datetime_format)
    assert data['created_tsp'] == event.created.timestamp()
    assert data['updated'] == event.updated.strftime(datetime_format)
    assert data['updated_tsp'] == event.updated.timestamp()


def test_retrieve__comment__with_attachment__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.current_task_instance
    due_date = timezone.now() + timedelta(hours=1)
    task.due_date = due_date
    task.save(update_fields=['due_date'])

    text = 'Some comment'
    attachment = FileAttachment.objects.create(
        name='filename.png',
        url='https://path.to.file/filename.png',
        size=141352,
        account_id=user.account_id,
    )
    event = WorkflowEventService.comment_created_event(
        workflow=workflow,
        user=user,
        text=text,
        attachments=[attachment.id],
        after_create_actions=False
    )
    attachment.event = event
    attachment.save()

    # act
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data = response.data[0]
    assert data['id'] == event.id
    str_datetime = event.created.strftime(datetime_format)
    assert data['created'] == str_datetime
    assert data['created_tsp'] == event.created.timestamp()
    assert data['updated'] is None
    assert data['status'] == CommentStatus.CREATED
    assert data['text'] == text
    assert data['type'] == WorkflowEventType.COMMENT
    assert data['user_id'] == user.id
    assert data['workflow_id'] == workflow.id
    assert data['task']['id'] == task.id
    assert data['task']['description'] == task.description
    assert data['task']['name'] == task.name
    assert data['task']['number'] == task.number
    str_due_date = due_date.strftime(datetime_format)
    assert data['task']['due_date'] == str_due_date
    assert data['task']['due_date_tsp'] == due_date.timestamp()
    assert data['task']['performers'] == [user.id]
    assert data['task']['output'] is None
    assert len(data['attachments']) == 1
    assert data['attachments'][0]['id'] == attachment.id
    assert data['attachments'][0]['name'] == attachment.name
    assert data['attachments'][0]['url'] == attachment.url
    assert data['attachments'][0]['thumbnail_url'] == attachment.thumbnail_url
    assert data['attachments'][0]['size'] == attachment.size
    assert data['watched'] == []
    assert data['reactions'] == {}


def test_retrieve__comment__with_watched__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    event = WorkflowEventService.comment_created_event(
        workflow=workflow,
        user=user,
        text='Some comment',
        after_create_actions=False
    )
    event.watched = [
        {
            'date':  timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'user_id': user.id
        }
    ]
    event.save()
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert response.status_code == 200
    data = response.data[0]
    assert len(data['watched']) == 1
    assert data['watched'][0]['date'] is not None
    assert data['watched'][0]['user_id'] == user.id


def test_retrieve__comment__with_reaction__ok(api_client):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    event = WorkflowEventService.comment_created_event(
        workflow=workflow,
        user=user,
        text='Some comment',
        after_create_actions=False
    )
    reaction = '=D'
    event.reactions = {
        reaction: [user.id],
    }
    event.save()
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert response.status_code == 200
    data = response.data[0]
    assert len(data['reactions']) == 1
    assert data['reactions'][reaction] == [user.id]


def test_retrieve__run_sub_workflow__ok(api_client):

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
        sub_workflow=sub_workflow,
        after_create_actions=False
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/workflows/{workflow.id}/events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    event_data = response.data[0]
    assert event_data['id'] == event.id
    assert event_data['created'] == event.created.strftime(datetime_format)
    assert event_data['created_tsp'] == event.created.timestamp()
    assert event_data['type'] == WorkflowEventType.SUB_WORKFLOW_RUN
    assert event_data['workflow_id'] == workflow.id

    task_data = event_data['task']
    assert task_data['id'] == ancestor_task.id
    assert task_data['description'] == ancestor_task.description
    assert task_data['name'] == ancestor_task.name
    assert task_data['number'] == ancestor_task.number
    assert task_data['due_date'] == (
        ancestor_task.due_date.strftime(datetime_format)
    )
    assert task_data['due_date_tsp'] == ancestor_task.due_date.timestamp()
    assert task_data['performers'] == [user.id]

    assert task_data['sub_workflow']['id'] == sub_workflow.id
    assert task_data['sub_workflow']['name'] == sub_workflow.name
    assert task_data['sub_workflow']['description'] == sub_workflow.description
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
