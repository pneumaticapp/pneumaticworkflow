import pytest
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from pneumatic_backend.notifications.enums import NotificationMethod
from pneumatic_backend.notifications.services.websockets import (
    WebSocketService
)
from pneumatic_backend.notifications.services.exceptions import (
    NotificationServiceError,
)
from pneumatic_backend.accounts.enums import UserType, NotificationType
from pneumatic_backend.accounts.models import Notification
from pneumatic_backend.processes.models import Delay
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_invited_user,
    create_test_workflow
)
from channels.testing import WebsocketCommunicator
from pneumatic_backend.asgi import application
from pneumatic_backend.consumers import PneumaticBaseConsumer


pytestmark = pytest.mark.django_db
datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'


def test_get_serialized_notification__type_mention__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    notification = Notification.objects.create(
        task=task,
        user=user,
        account=user.account,
        type=NotificationType.MENTION,
        text='some text',
    )
    service = WebSocketService()

    # act
    data = service._get_serialized_notification(notification)

    # assert
    assert data['id'] == notification.id
    assert data['text'] == notification.text
    assert data['type'] == notification.type
    assert data['datetime']
    assert data['status'] == notification.status
    assert data['author'] == notification.author
    assert data['task']['id'] == task.id
    assert data['task']['name'] == task.name
    assert data['workflow']['id'] == workflow.id
    assert data['workflow']['name'] == workflow.name
    assert data['text'] == notification.text


def test_get_serialized_notification__type_delay__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.first()
    Delay.objects.create(
        task=task,
        start_date=timezone.now(),
        duration=timedelta(days=1)
    )
    notification = Notification.objects.create(
        task_id=task.id,
        user_id=user.id,
        account_id=user.account.id,
        type=NotificationType.DELAY_WORKFLOW,
        text='text',
    )
    service = WebSocketService()

    # act
    data = service._get_serialized_notification(notification)

    # assert
    assert data['id'] == notification.id
    assert data['text'] == notification.text
    assert data['type'] == notification.type
    assert data['datetime'] is not None
    assert data['status'] == notification.status
    assert data['author'] == notification.author
    assert data['task']['id'] == task.id
    assert data['task']['name'] == task.name
    assert data['task']['delay']['estimated_end_date'] is not None
    assert data['task']['delay']['duration'] == '1 00:00:00'
    assert data['workflow']['id'] == workflow.id
    assert data['workflow']['name'] == workflow.name


def test_get_serialized_notification__type_due_date__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.first()
    task.due_date = timezone.now() + timedelta(hours=1)
    task.save(update_fields=['due_date'])
    notification = Notification.objects.create(
        task_id=task.id,
        user_id=user.id,
        account_id=user.account.id,
        type=NotificationType.DUE_DATE_CHANGED,
    )
    service = WebSocketService()

    # act
    data = service._get_serialized_notification(notification)

    # assert
    assert data['id'] == notification.id
    assert data['type'] == NotificationType.DUE_DATE_CHANGED
    str_due_date = task.due_date.strftime(datetime_format)
    assert data['task']['due_date'] == str_due_date


def test_async_send__ok(mocker):

    # arrange
    get_channel_layer_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'get_channel_layer',
        return_value=mocker.Mock()
    )
    get_event_loop_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'get_event_loop'
    )
    create_task_mock = mocker.Mock()
    get_event_loop_mock.create_task = mocker.Mock(
        return_value=create_task_mock
    )
    group_name = 'group'
    data = {'some': 'data'}
    service = WebSocketService()

    # act
    service._async_send(
        group_name=group_name,
        data=data
    )

    # assert
    get_channel_layer_mock.assert_called_once()
    get_event_loop_mock.assert_called_once()


def test_send__sync__ok(mocker):

    # arrange
    sync_send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._sync_send',
    )
    group_name = 'group'
    data = {'some': 'data'}
    service = WebSocketService()

    # act
    service._send(
        sync=True,
        group_name=group_name,
        method_name=NotificationMethod.overdue_task,
        data=data
    )

    # assert
    sync_send_mock.assert_called_once_with(
        group_name=group_name,
        data=data
    )


def test_send__async__ok(mocker):

    # arrange
    async_send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._async_send',
    )
    group_name = 'group'
    data = {'some': 'data'}
    service = WebSocketService()

    # act
    service._send(
        group_name=group_name,
        method_name=NotificationMethod.overdue_task,
        data=data
    )

    # assert
    async_send_mock.assert_called_once_with(
        group_name=group_name,
        data=data
    )


def test_send__not_allowed_method__raise_exception(mocker):

    # arrange
    mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.ALLOWED_METHODS',
        {NotificationMethod.new_task}
    )
    sync_send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._sync_send',
    )
    async_send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._async_send',
    )
    group_name = 'group'
    data = {'some': 'data'}
    service = WebSocketService()

    # act
    with pytest.raises(NotificationServiceError) as ex:
        service._send(
            group_name=group_name,
            method_name=NotificationMethod.overdue_task,
            data=data
        )

    # assert
    assert ex.value.message == (
        f'{NotificationMethod.overdue_task} is not allowed notification'
    )
    sync_send_mock.assert_not_called()
    async_send_mock.assert_not_called()


def test_send_overdue_task__type_user__ok(mocker):

    # arrange
    user_id = 12
    user_type = UserType.USER
    notification = mocker.Mock
    data = {'some': 'body'}
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._send'
    )
    slz_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._get_serialized_notification',
        return_value=data
    )

    service = WebSocketService()

    # act
    service.send_overdue_task(
        user_id=user_id,
        user_type=user_type,
        notification=notification,
        sync=True
    )

    # assert
    send_mock.assert_called_once_with(
        method_name=NotificationMethod.overdue_task,
        group_name=f'notifications_{user_id}',
        data=data,
        sync=True
    )
    slz_mock.assert_called_once_with(notification)


def test_send_overdue_task__type_guest__not_sent(mocker):

    # arrange
    user_id = 12
    user_type = UserType.GUEST
    notification = mocker.Mock
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._send'
    )

    service = WebSocketService()

    # act
    service.send_overdue_task(
        user_id=user_id,
        user_type=user_type,
        notification=notification,
        sync=True
    )

    # assert
    send_mock.assert_not_called()


def test_send_resume_workflow__ok(mocker):

    # arrange
    user_id = 12
    notification = mocker.Mock
    data = {'some': 'body'}
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._send'
    )
    slz_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._get_serialized_notification',
        return_value=data
    )

    service = WebSocketService()

    # act
    service.send_resume_workflow(
        user_id=user_id,
        sync=True,
        notification=notification,
    )

    # assert
    send_mock.assert_called_once_with(
        method_name=NotificationMethod.resume_workflow,
        group_name=f'notifications_{user_id}',
        data=data,
        sync=True
    )
    slz_mock.assert_called_once_with(notification)


def test_send_delay_workflow__ok(mocker):

    # arrange
    user_id = 12
    notification = mocker.Mock
    data = {'some': 'body'}
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._send'
    )
    slz_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._get_serialized_notification',
        return_value=data
    )

    service = WebSocketService()

    # act
    service.send_delay_workflow(
        user_id=user_id,
        sync=False,
        notification=notification,
    )

    # assert
    send_mock.assert_called_once_with(
        method_name=NotificationMethod.delay_workflow,
        group_name=f'notifications_{user_id}',
        data=data,
        sync=False
    )
    slz_mock.assert_called_once_with(notification)


def test_send_due_date_changed__type_user__ok(mocker):

    # arrange
    user_id = 12
    user_type = UserType.USER
    notification = mocker.Mock
    data = {'some': 'body'}
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._send'
    )
    slz_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._get_serialized_notification',
        return_value=data
    )

    service = WebSocketService()

    # act
    service.send_due_date_changed(
        user_id=user_id,
        user_type=user_type,
        notification=notification,
        sync=True
    )

    # assert
    send_mock.assert_called_once_with(
        method_name=NotificationMethod.due_date_changed,
        group_name=f'notifications_{user_id}',
        data=data,
        sync=True
    )
    slz_mock.assert_called_once_with(notification)


def test_send_due_date_changed__type_guest__not_sent(mocker):

    # arrange
    user_id = 12
    user_type = UserType.GUEST
    notification = mocker.Mock
    data = {'some': 'body'}
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._send'
    )
    slz_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._get_serialized_notification',
        return_value=data
    )

    service = WebSocketService()

    # act
    service.send_due_date_changed(
        user_id=user_id,
        user_type=user_type,
        notification=notification,
        sync=True
    )

    # assert
    send_mock.assert_not_called()
    slz_mock.assert_not_called()


@pytest.mark.asyncio
async def test_consumer_send_notification__received(mocker, api_client):

    # arrange
    user = create_test_user()
    invited = create_invited_user(user)
    token = '123456'
    workflow = create_test_workflow(user)
    notification = Notification.objects.create(
        task=workflow.current_task_instance,
        user=user,
        author=invited,
        account=user.account,
        type=NotificationType.COMMENT,
        text='Comment text'
    )
    service = WebSocketService()

    ws_auth_patch = mocker.patch(
        'pneumatic_backend.authentication.'
        'middleware.PneumaticToken.get_user_from_token',
        return_value=user
    )
    communicator = WebsocketCommunicator(
        application,
        f'/ws/notifications/?auth_token={token}',
    )
    await communicator.connect()

    service.send_comment(
        user_id=user.id,
        sync=False,
        notification=notification
    )

    # act
    response = await communicator.receive_json_from()

    # assert
    assert response['id'] == notification.id
    assert response['text'] == notification.text
    assert response['author'] == invited.id
    assert response['workflow']['id'] == workflow.id

    await communicator.disconnect()
    ws_auth_patch.assert_called_once_with(token)


@pytest.mark.asyncio
async def test_consumer__connection__ok(mocker):
    user = create_test_user()
    user_patch = mocker.patch(
        'pneumatic_backend.authentication.'
        'middleware.PneumaticToken.get_user_from_token'
    )
    user_patch.return_value = user
    communicator = WebsocketCommunicator(
        application,
        '/ws/notifications/?auth_token=123456'
    )

    connected, _ = await communicator.connect()

    assert connected is True
    user_patch.assert_called_with('123456')

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_consumer__incorrect_token__deny_connection(mocker):
    user_patch = mocker.patch(
        'pneumatic_backend.authentication.'
        'middleware.PneumaticToken.get_user_from_token'
    )
    user_patch.side_effect = ObjectDoesNotExist()
    communicator = WebsocketCommunicator(
        application,
        '/ws/notifications/?auth_token=123456',
    )

    connected, _ = await communicator.connect()

    assert connected is False

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_consumer__without_token__deny_connection(mocker):
    user_patch = mocker.patch(
        'pneumatic_backend.authentication.'
        'middleware.PneumaticToken.get_user_from_token'
    )
    communicator = WebsocketCommunicator(
        application,
        '/ws/notifications/',
    )

    connected, _ = await communicator.connect()

    assert connected is False
    user_patch.assert_not_called()
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_consumer__ping_pong__ok(mocker, api_client):

    # arrange
    user = create_test_user()
    user_patch = mocker.patch(
        'pneumatic_backend.authentication.'
        'middleware.PneumaticToken.get_user_from_token'
    )
    user_patch.return_value = user
    communicator = WebsocketCommunicator(
        application,
        '/ws/notifications/?auth_token=123456',
    )
    await communicator.connect()

    # act
    await communicator.send_to(
        text_data=PneumaticBaseConsumer.HEARTBEAT_PING_MESSAGE
    )

    # assert
    response = await communicator.receive_output()
    assert response['text'] == PneumaticBaseConsumer.HEARTBEAT_PONG_MESSAGE
    await communicator.disconnect()


def test_send_urgent__ok(mocker):

    # arrange
    user_id = 12
    notification = mocker.Mock()
    data = {'some': 'body'}
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._send'
    )
    slz_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._get_serialized_notification',
        return_value=data
    )

    service = WebSocketService()

    # act
    service.send_urgent(
        user_id=user_id,
        notification=notification,
        sync=True
    )

    # assert
    send_mock.assert_called_once_with(
        method_name=NotificationMethod.urgent,
        group_name=f'notifications_{user_id}',
        data=data,
        sync=True
    )
    slz_mock.assert_called_once_with(notification)


def test_send_not_urgent__ok(mocker):

    # arrange
    user_id = 12
    notification = mocker.Mock()
    data = {'some': 'body'}
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._send'
    )
    slz_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._get_serialized_notification',
        return_value=data
    )

    service = WebSocketService()

    # act
    service.send_not_urgent(
        user_id=user_id,
        notification=notification,
        sync=True
    )

    # assert
    send_mock.assert_called_once_with(
        method_name=NotificationMethod.not_urgent,
        group_name=f'notifications_{user_id}',
        data=data,
        sync=True
    )
    slz_mock.assert_called_once_with(notification)


def test_send_mention__ok(mocker):

    # arrange
    user_id = 12
    notification = mocker.Mock()
    data = {'some': 'body'}
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._send'
    )
    slz_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._get_serialized_notification',
        return_value=data
    )

    service = WebSocketService()

    # act
    service.send_mention(
        user_id=user_id,
        notification=notification,
        sync=True
    )

    # assert
    send_mock.assert_called_once_with(
        method_name=NotificationMethod.mention,
        group_name=f'notifications_{user_id}',
        data=data,
        sync=True
    )
    slz_mock.assert_called_once_with(notification)


def test_send_comment__ok(mocker):

    # arrange
    user_id = 12
    notification = mocker.Mock()
    data = {'some': 'body'}
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._send'
    )
    slz_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._get_serialized_notification',
        return_value=data
    )

    service = WebSocketService()

    # act
    service.send_comment(
        user_id=user_id,
        notification=notification,
        sync=True
    )

    # assert
    send_mock.assert_called_once_with(
        method_name=NotificationMethod.comment,
        group_name=f'notifications_{user_id}',
        data=data,
        sync=True
    )
    slz_mock.assert_called_once_with(notification)


def test_send_system__ok(mocker):

    # arrange
    user_id = 12
    notification = mocker.Mock()
    data = {'some': 'body'}
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._send'
    )
    slz_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._get_serialized_notification',
        return_value=data
    )

    service = WebSocketService()

    # act
    service.send_system(
        user_id=user_id,
        notification=notification,
        sync=True
    )

    # assert
    send_mock.assert_called_once_with(
        method_name=NotificationMethod.system,
        group_name=f'notifications_{user_id}',
        data=data,
        sync=True
    )
    slz_mock.assert_called_once_with(notification)


def test_send_reaction__ok(mocker):

    # arrange
    user_id = 12
    notification = mocker.Mock()
    data = {'some': 'body'}
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._send'
    )
    slz_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._get_serialized_notification',
        return_value=data
    )

    service = WebSocketService()

    # act
    service.send_reaction(
        user_id=user_id,
        notification=notification,
        sync=True
    )

    # assert
    send_mock.assert_called_once_with(
        method_name=NotificationMethod.reaction,
        group_name=f'notifications_{user_id}',
        data=data,
        sync=True
    )
    slz_mock.assert_called_once_with(notification)


def test_send_complete_task__ok(mocker):

    # arrange
    user_id = 12
    notification = mocker.Mock()
    data = {'some': 'body'}
    send_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._send'
    )
    slz_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService._get_serialized_notification',
        return_value=data
    )

    service = WebSocketService()

    # act
    service.send_complete_task(
        user_id=user_id,
        notification=notification,
        sync=True
    )

    # assert
    send_mock.assert_called_once_with(
        method_name=NotificationMethod.complete_task,
        group_name=f'notifications_{user_id}',
        data=data,
        sync=True
    )
    slz_mock.assert_called_once_with(notification)
