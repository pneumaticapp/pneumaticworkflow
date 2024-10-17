import pytest
from pneumatic_backend.processes.enums import (
    DirectlyStatus
)
from pneumatic_backend.processes.models import (
    TaskPerformer
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_account,
    create_test_guest,
)
from pneumatic_backend.notifications.tasks import (
    _send_workflow_event
)
from pneumatic_backend.processes.api_v2.serializers.workflow.events import (
    WorkflowEventSerializer,
)
from pneumatic_backend.processes.api_v2.services.events import (
    WorkflowEventService
)


pytestmark = pytest.mark.django_db


def test_send_workflow_event__system_task_event__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    member = create_test_user(
        email='member@test.test',
        account=account,
        is_admin=False,
        is_account_owner=False
    )
    create_test_user(
        email='not_member@test.test',
        account=account,
        is_account_owner=False
    )
    create_test_user(email='another@test.test')
    guest = create_test_guest(account=account)

    workflow = create_test_workflow(account_owner, tasks_count=1)
    workflow.members.add(member)
    task = workflow.current_task_instance
    task.performers.add(guest)

    event = WorkflowEventService.task_started_event(task)
    data = WorkflowEventSerializer(instance=event).data
    websocket_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_workflow_event'
    )

    # act
    _send_workflow_event(data=data)

    # assert
    websocket_notification_mock.call_count = 3
    websocket_notification_mock.has_calls([
        mocker.call(
            user_id=account_owner.id,
            sync=True,
            data=data,
        ),
        mocker.call(
            user_id=member.id,
            sync=True,
            data=data,
        ),
        mocker.call(
            user_id=guest.id,
            sync=True,
            data=data,
        )
    ])


def test_send_workflow_event__system_workflow_event__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    member = create_test_user(
        email='member@test.test',
        account=account,
        is_admin=False,
        is_account_owner=False
    )
    create_test_user(
        email='not_member@test.test',
        account=account,
        is_account_owner=False
    )
    create_test_user(email='another@test.test')
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    workflow.members.add(member)
    task = workflow.current_task_instance
    task.performers.add(guest)

    event = WorkflowEventService.workflow_ended_event(
        user=account_owner,
        workflow=workflow
    )
    data = WorkflowEventSerializer(instance=event).data
    websocket_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_workflow_event'
    )

    # act
    _send_workflow_event(data=data)

    # assert
    websocket_notification_mock.call_count = 2
    websocket_notification_mock.has_calls([
        mocker.call(
            user_id=account_owner.id,
            sync=True,
            data=data,
        ),
        mocker.call(
            user_id=member.id,
            sync=True,
            data=data,
        )
    ])


def test_send_workflow_event__user_task_event__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    member = create_test_user(
        email='member@test.test',
        account=account,
        is_admin=False,
        is_account_owner=False
    )
    create_test_user(
        email='not_member@test.test',
        account=account,
        is_account_owner=False
    )
    create_test_user(email='another@test.test')
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    workflow.members.add(member)
    task = workflow.current_task_instance
    task.performers.add(guest)

    event = WorkflowEventService.task_complete_event(
        user=account_owner,
        task=task
    )
    data = WorkflowEventSerializer(instance=event).data
    websocket_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_workflow_event'
    )

    # act
    _send_workflow_event(data=data)

    # assert
    websocket_notification_mock.call_count = 3
    websocket_notification_mock.has_calls([
        mocker.call(
            user_id=account_owner.id,
            sync=True,
            data=data,
        ),
        mocker.call(
            user_id=member.id,
            sync=True,
            data=data,
        ),
        mocker.call(
            user_id=guest.id,
            sync=True,
            data=data,
        )
    ])


def test_send_workflow_event__comment_event__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    member = create_test_user(
        email='member@test.test',
        account=account,
        is_admin=False,
        is_account_owner=False
    )
    create_test_user(
        email='not_member@test.test',
        account=account,
        is_account_owner=False
    )
    create_test_user(email='another@test.test')
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    workflow.members.add(member)
    task = workflow.current_task_instance
    task.performers.add(guest)

    event = WorkflowEventService.comment_created_event(
        user=account_owner,
        workflow=workflow,
        text='Some text',
        after_create_actions=False
    )
    data = WorkflowEventSerializer(instance=event).data
    websocket_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_workflow_event'
    )

    # act
    _send_workflow_event(data=data)

    # assert
    websocket_notification_mock.call_count = 3
    websocket_notification_mock.has_calls([
        mocker.call(
            user_id=account_owner.id,
            sync=True,
            data=data,
        ),
        mocker.call(
            user_id=member.id,
            sync=True,
            data=data,
        ),
        mocker.call(
            user_id=guest.id,
            sync=True,
            data=data,
        )
    ])


def test_send_workflow_event__directly_deleted_guest__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )

    guest = create_test_guest(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    TaskPerformer.objects.create(
        task=task,
        user=guest,
        directly_status=DirectlyStatus.DELETED
    )

    event = WorkflowEventService.comment_created_event(
        user=account_owner,
        workflow=workflow,
        text='Some text',
        after_create_actions=False
    )
    data = WorkflowEventSerializer(instance=event).data
    websocket_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_workflow_event'
    )

    # act
    _send_workflow_event(data=data)

    # assert
    websocket_notification_mock.call_count = 1
    websocket_notification_mock.has_calls([
        mocker.call(
            user_id=account_owner.id,
            sync=True,
            data=data,
        )
    ])


def test_send_workflow_event__another_task_guest__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=3)
    workflow.current_task = 2
    workflow.save()

    task_1 = workflow.tasks.get(number=1)
    guest_1 = create_test_guest(account=account, email='guest-1@t.t')
    task_1.performers.add(guest_1)

    task_2 = workflow.tasks.get(number=2)
    guest_2 = create_test_guest(account=account, email='guest-2@t.t')
    task_2.performers.add(guest_2)

    task_3 = workflow.tasks.get(number=3)
    guest_3 = create_test_guest(account=account, email='guest-3@t.t')
    task_3.performers.add(guest_3)

    event = WorkflowEventService.comment_created_event(
        user=account_owner,
        workflow=workflow,
        text='Some text',
        after_create_actions=False
    )
    data = WorkflowEventSerializer(instance=event).data
    websocket_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_workflow_event'
    )

    # act
    _send_workflow_event(data=data)

    # assert
    websocket_notification_mock.call_count = 2
    websocket_notification_mock.has_calls([
        mocker.call(
            user_id=account_owner.id,
            sync=True,
            data=data,
        ),
        mocker.call(
            user_id=guest_2.id,
            sync=True,
            data=data,
        )
    ])


def test_send_workflow_event__another_account_guest__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    event = WorkflowEventService.comment_created_event(
        user=account_owner,
        workflow=workflow,
        text='Some text',
        after_create_actions=False
    )
    data = WorkflowEventSerializer(instance=event).data

    another_account = create_test_account()
    another_account_owner = create_test_user(
        is_account_owner=True,
        account=another_account,
        email='another@test.test'
    )
    another_workflow = create_test_workflow(
        another_account_owner,
        tasks_count=1
    )
    guest = create_test_guest(account=another_account)

    task = another_workflow.current_task_instance
    task.performers.add(guest)

    websocket_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_workflow_event'
    )

    # act
    _send_workflow_event(data=data)

    # assert
    websocket_notification_mock.call_count = 1
    websocket_notification_mock.has_calls([
        mocker.call(
            user_id=account_owner.id,
            sync=True,
            data=data,
        )
    ])
