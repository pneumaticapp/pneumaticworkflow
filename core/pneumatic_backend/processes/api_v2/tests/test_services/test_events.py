import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
)
from pneumatic_backend.processes.enums import (
    WorkflowEventType,
    CommentStatus,
)
from pneumatic_backend.processes.api_v2.services import WorkflowEventService
from pneumatic_backend.processes.models import (
    FileAttachment,
    WorkflowEvent,
)
from pneumatic_backend.processes.api_v2.serializers.workflow.events import (
    WorkflowEventSerializer,
)
from pneumatic_backend.utils.dates import date_format


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_after_create_actions(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user)
    event = WorkflowEvent.objects.create(
        account=user.account,
        type=WorkflowEventType.COMMENT,
        text='Some text',
        with_attachments=False,
        workflow=workflow,
        user=user,
    )
    data = WorkflowEventSerializer(event).data
    send_workflow_event_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'send_workflow_event.delay'
    )

    # act
    WorkflowEventService._after_create_actions(event)

    # assert
    send_workflow_event_mock.assert_called_once_with(data=data)


def test_comment_created_event__ok(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        tasks_count=1
    )
    task = workflow.current_task_instance
    text = (
        "(![avatar.jpg](https://storage.com/dev/avatar.jpg "
        "\"attachment_id:3349 entityType:image\")"
    )
    attach = FileAttachment.objects.create(
        account_id=user.account_id,
        name='filename.png',
        size=384812,
        url='https://storage.com/dev/avatar.jpg',
    )
    after_create_actions_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'WorkflowEventService._after_create_actions'
    )

    # act
    event = WorkflowEventService.comment_created_event(
        user=user,
        workflow=workflow,
        text=text,
        attachments=[attach.id],
    )

    # assert
    assert event.account == user.account
    assert event.created
    assert event.type == WorkflowEventType.COMMENT
    assert event.text == text
    assert event.workflow == workflow
    assert event.user == user
    assert event.with_attachments is True
    assert event.status == CommentStatus.CREATED
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id
    assert event.task_json['id'] == task.id
    assert event.task_json['number'] == 1
    assert event.task_json['name'] == task.name
    assert event.task_json['description'] == task.description
    assert event.task_json['performers'] == [user.id]
    assert event.task_json['due_date'] is None
    assert event.task_json['output'] is None
    after_create_actions_mock.assert_called_once_with(event)


def test_sub_workflow_run_event__ok(mocker):

    # arrange
    after_create_actions_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'WorkflowEventService._after_create_actions'
    )
    user = create_test_user()
    workflow = create_test_workflow(
        name='Parent workflow',
        user=user,
        tasks_count=1
    )
    ancestor_task = workflow.current_task_instance
    ancestor_task.name = 'Ancestor task name'
    ancestor_task.description = 'Ancestor task desc'
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

    # act
    event = WorkflowEventService.sub_workflow_run_event(
        user=user,
        workflow=workflow,
        sub_workflow=sub_workflow,
    )

    # assert
    assert event.account == user.account
    assert event.created
    assert event.type == WorkflowEventType.SUB_WORKFLOW_RUN
    assert event.workflow == workflow
    assert event.user == user
    assert event.workflow_id == workflow.id
    assert event.task_id == ancestor_task.id
    assert event.task_json['id'] == ancestor_task.id
    assert event.task_json['number'] == 1
    assert event.task_json['name'] == ancestor_task.name
    assert event.task_json['description'] == ancestor_task.description
    assert event.task_json['performers'] == [user.id]
    sub_workflow_data = event.task_json['sub_workflow']
    assert sub_workflow_data['id'] == sub_workflow.id
    assert sub_workflow_data['name'] == sub_workflow.name
    assert sub_workflow_data['description'] == sub_workflow.description
    assert sub_workflow_data['date_created'] == (
        sub_workflow.date_created.strftime(date_format)
    )
    assert sub_workflow_data['date_created_tsp'] == (
        sub_workflow.date_created.timestamp()
    )
    assert sub_workflow_data['due_date'] == (
        sub_workflow.due_date.strftime(date_format)
    )
    assert sub_workflow_data['due_date_tsp'] == (
        sub_workflow.due_date.timestamp()
    )
    assert sub_workflow_data['is_urgent'] == (
        sub_workflow.is_urgent
    )
    after_create_actions_mock.assert_called_once_with(event)


def test_sub_workflow_run_event__skip_after_create_actions__ok(mocker):

    # arrange
    after_create_actions_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.events.'
        'WorkflowEventService._after_create_actions'
    )
    user = create_test_user()
    workflow = create_test_workflow(
        name='Parent workflow',
        user=user,
        tasks_count=1
    )
    ancestor_task = workflow.current_task_instance
    sub_workflow = create_test_workflow(
        user=user,
        ancestor_task=ancestor_task,
    )

    # act
    event = WorkflowEventService.sub_workflow_run_event(
        user=user,
        workflow=workflow,
        sub_workflow=sub_workflow,
        after_create_actions=False
    )

    # assert
    assert event.workflow_id == workflow.id
    assert event.task_json['id'] == ancestor_task.id
    sub_workflow_data = event.task_json['sub_workflow']
    assert sub_workflow_data['id'] == sub_workflow.id
    after_create_actions_mock.assert_not_called()
