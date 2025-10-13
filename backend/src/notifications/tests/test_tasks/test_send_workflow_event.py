import pytest
from src.processes.enums import (
    DirectlyStatus,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_account,
    create_test_guest,
)
from src.notifications.tasks import (
    _send_workflow_event,
)
from src.processes.serializers.workflows.events import (
    WorkflowEventSerializer,
)
from src.processes.services.events import (
    WorkflowEventService,
)
from src.notifications.services.websockets import (
    WebSocketService,
)


pytestmark = pytest.mark.django_db


def test_send_workflow_event__system_task_event__ok(mocker):

    # arrange
    account = create_test_account(
        logo_lg='https://best.com/logo.jpg',
        log_api_requests=True,
    )
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    member = create_test_user(
        email='member@test.test',
        account=account,
        is_admin=False,
        is_account_owner=False,
    )
    create_test_user(
        email='not_member@test.test',
        account=account,
        is_account_owner=False,
    )
    create_test_user(email='another@test.test')
    guest = create_test_guest(account=account)

    workflow = create_test_workflow(account_owner, tasks_count=1)
    workflow.members.add(member)
    task = workflow.tasks.get(number=1)
    task.performers.add(guest)

    event = WorkflowEventService.task_started_event(
        task=task,
        after_create_actions=False,
    )
    data = WorkflowEventSerializer(instance=event).data
    websocket_service_init_mock = mocker.patch.object(
        WebSocketService,
        attribute='__init__',
        return_value=None,
    )
    websocket_notification_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_workflow_event',
    )

    # act
    _send_workflow_event(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
        data=data,
    )

    # assert
    websocket_notification_mock.call_count = 3
    websocket_service_init_mock.call_count = 3
    websocket_service_init_mock.has_calls([
        mocker.call(
            logo_lg=account.logo_lg,
            account_id=account.id,
            logging=account.log_api_requests,
        ),
        mocker.call(
            logo_lg=account.logo_lg,
            account_id=account.id,
            logging=account.log_api_requests,
        ),
        mocker.call(
            logo_lg=account.logo_lg,
            account_id=account.id,
            logging=account.log_api_requests,
        ),
    ])
    websocket_notification_mock.has_calls([
        mocker.call(
            user_id=account_owner.id,
            user_email=account_owner.email,
            sync=True,
            data=data,
        ),
        mocker.call(
            user_id=member.id,
            user_email=member.email,
            sync=True,
            data=data,
        ),
        mocker.call(
            user_id=guest.id,
            user_email=guest.email,
            sync=True,
            data=data,
        ),
    ])


def test_send_workflow_event__system_workflow_event__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    member = create_test_user(
        email='member@test.test',
        account=account,
        is_admin=False,
        is_account_owner=False,
    )
    create_test_user(
        email='not_member@test.test',
        account=account,
        is_account_owner=False,
    )
    create_test_user(email='another@test.test')
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    workflow.members.add(member)
    task = workflow.tasks.get(number=1)
    task.performers.add(guest)

    event = WorkflowEventService.workflow_ended_event(
        user=account_owner,
        workflow=workflow,
        after_create_actions=False,
    )
    data = WorkflowEventSerializer(instance=event).data
    websocket_service_init_mock = mocker.patch.object(
        WebSocketService,
        attribute='__init__',
        return_value=None,
    )
    websocket_notification_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_workflow_event',
    )

    # act
    _send_workflow_event(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
        data=data,
    )

    # assert
    websocket_notification_mock.call_count = 2
    websocket_service_init_mock.call_count = 2
    websocket_service_init_mock.has_calls([
        mocker.call(
            logo_lg=account.logo_lg,
            account_id=account.id,
            logging=account.log_api_requests,
        ),
        mocker.call(
            logo_lg=account.logo_lg,
            account_id=account.id,
            logging=account.log_api_requests,
        ),
    ])
    websocket_notification_mock.has_calls([
        mocker.call(
            user_id=account_owner.id,
            user_email=account_owner.email,
            sync=True,
            data=data,
        ),
        mocker.call(
            user_id=member.id,
            user_email=member.email,
            sync=True,
            data=data,
        ),
    ])


def test_send_workflow_event__user_task_event__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    member = create_test_user(
        email='member@test.test',
        account=account,
        is_admin=False,
        is_account_owner=False,
    )
    create_test_user(
        email='not_member@test.test',
        account=account,
        is_account_owner=False,
    )
    create_test_user(email='another@test.test')
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    workflow.members.add(member)
    task = workflow.tasks.get(number=1)
    task.performers.add(guest)

    event = WorkflowEventService.task_complete_event(
        user=account_owner,
        task=task,
        after_create_actions=False,
    )
    data = WorkflowEventSerializer(instance=event).data
    websocket_service_init_mock = mocker.patch.object(
        WebSocketService,
        attribute='__init__',
        return_value=None,
    )
    websocket_notification_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_workflow_event',
    )

    # act
    _send_workflow_event(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
        data=data,
    )

    # assert
    websocket_notification_mock.call_count = 3
    websocket_service_init_mock.call_count = 3
    websocket_service_init_mock.has_calls([
        mocker.call(
            logo_lg=account.logo_lg,
            account_id=account.id,
            logging=account.log_api_requests,
        ),
        mocker.call(
            logo_lg=account.logo_lg,
            account_id=account.id,
            logging=account.log_api_requests,
        ),
        mocker.call(
            logo_lg=account.logo_lg,
            account_id=account.id,
            logging=account.log_api_requests,
        ),
    ])
    websocket_notification_mock.has_calls([
        mocker.call(
            user_id=account_owner.id,
            user_email=account_owner.email,
            sync=True,
            data=data,
        ),
        mocker.call(
            user_id=member.id,
            user_email=member.email,
            sync=True,
            data=data,
        ),
        mocker.call(
            user_id=guest.id,
            user_email=guest.email,
            sync=True,
            data=data,
        ),
    ])


def test_send_workflow_event__comment_event__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    member = create_test_user(
        email='member@test.test',
        account=account,
        is_admin=False,
        is_account_owner=False,
    )
    create_test_user(
        email='not_member@test.test',
        account=account,
        is_account_owner=False,
    )
    create_test_user(email='another@test.test')
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    workflow.members.add(member)
    task = workflow.tasks.get(number=1)
    task.performers.add(guest)

    event = WorkflowEventService.comment_created_event(
        user=account_owner,
        task=workflow.tasks.get(number=1),
        text='Some text',
        after_create_actions=False,
    )
    data = WorkflowEventSerializer(instance=event).data
    websocket_service_init_mock = mocker.patch.object(
        WebSocketService,
        attribute='__init__',
        return_value=None,
    )
    websocket_notification_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_workflow_event',
    )

    # act
    _send_workflow_event(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
        data=data,
    )

    # assert
    websocket_notification_mock.call_count = 3
    websocket_service_init_mock.call_count = 3
    websocket_service_init_mock.has_calls([
        mocker.call(
            logo_lg=account.logo_lg,
            account_id=account.id,
            logging=account.log_api_requests,
        ),
        mocker.call(
            logo_lg=account.logo_lg,
            account_id=account.id,
            logging=account.log_api_requests,
        ),
        mocker.call(
            logo_lg=account.logo_lg,
            account_id=account.id,
            logging=account.log_api_requests,
        ),
    ])
    websocket_notification_mock.has_calls([
        mocker.call(
            user_id=account_owner.id,
            user_email=account_owner.email,
            sync=True,
            data=data,
        ),
        mocker.call(
            user_id=member.id,
            user_email=member.email,
            sync=True,
            data=data,
        ),
        mocker.call(
            user_id=guest.id,
            user_email=guest.email,
            sync=True,
            data=data,
        ),
    ])


def test_send_workflow_event__directly_deleted_guest__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )

    guest = create_test_guest(account=account)
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task=task,
        user=guest,
        directly_status=DirectlyStatus.DELETED,
    )

    event = WorkflowEventService.comment_created_event(
        user=account_owner,
        task=task,
        text='Some text',
        after_create_actions=False,
    )
    data = WorkflowEventSerializer(instance=event).data
    websocket_service_init_mock = mocker.patch.object(
        WebSocketService,
        attribute='__init__',
        return_value=None,
    )
    websocket_notification_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_workflow_event',
    )

    # act
    _send_workflow_event(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
        data=data,
    )

    # assert
    websocket_service_init_mock.call_count = 1
    websocket_notification_mock.call_count = 1
    websocket_service_init_mock.has_calls([
        mocker.call(
            logo_lg=account.logo_lg,
            account_id=account.id,
            logging=account.log_api_requests,
        ),
    ])
    websocket_notification_mock.has_calls([
        mocker.call(
            user_id=account_owner.id,
            user_email=account_owner.email,
            sync=True,
            data=data,
        ),
    ])


def test_send_workflow_event__another_task_guest__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    workflow = create_test_workflow(
        account_owner,
        tasks_count=3,
        active_task_number=2,
    )

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
        task=workflow.tasks.get(number=1),
        text='Some text',
        after_create_actions=False,
    )
    data = WorkflowEventSerializer(instance=event).data
    websocket_service_init_mock = mocker.patch.object(
        WebSocketService,
        attribute='__init__',
        return_value=None,
    )
    websocket_notification_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_workflow_event',
    )

    # act
    _send_workflow_event(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
        data=data,
    )

    # assert
    websocket_notification_mock.call_count = 2
    websocket_service_init_mock.call_count = 2
    websocket_service_init_mock.has_calls([
        mocker.call(
            logo_lg=account.logo_lg,
            account_id=account.id,
            logging=account.log_api_requests,
        ),
        mocker.call(
            logo_lg=account.logo_lg,
            account_id=account.id,
            logging=account.log_api_requests,
        ),
    ])
    websocket_notification_mock.has_calls([
        mocker.call(
            user_id=account_owner.id,
            user_email=account_owner.email,
            sync=True,
            data=data,
        ),
        mocker.call(
            user_id=guest_2.id,
            user_email=guest_2.email,
            sync=True,
            data=data,
        ),
    ])


def test_send_workflow_event__another_account_guest__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    event = WorkflowEventService.comment_created_event(
        user=account_owner,
        task=workflow.tasks.get(number=1),
        text='Some text',
        after_create_actions=False,
    )
    data = WorkflowEventSerializer(instance=event).data

    another_account = create_test_account()
    another_account_owner = create_test_user(
        is_account_owner=True,
        account=another_account,
        email='another@test.test',
    )
    another_workflow = create_test_workflow(
        another_account_owner,
        tasks_count=1,
    )
    guest = create_test_guest(account=another_account)

    task = another_workflow.tasks.get(number=1)
    task.performers.add(guest)
    websocket_service_init_mock = mocker.patch.object(
        WebSocketService,
        attribute='__init__',
        return_value=None,
    )
    websocket_notification_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_workflow_event',
    )

    # act
    _send_workflow_event(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
        data=data,
    )

    # assert
    websocket_notification_mock.call_count = 1
    websocket_service_init_mock.call_count = 1
    websocket_service_init_mock.has_calls([
        mocker.call(
            logo_lg=account.logo_lg,
            account_id=account.id,
            logging=account.log_api_requests,
        ),
    ])
    websocket_notification_mock.has_calls([
        mocker.call(
            user_id=account_owner.id,
            sync=True,
            data=data,
        ),
    ])
