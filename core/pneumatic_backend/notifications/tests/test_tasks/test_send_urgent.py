import pytest
from django.utils import timezone
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_account,
    create_test_guest,
)
from pneumatic_backend.notifications.tasks import (
    _send_urgent_notification
)
from pneumatic_backend.processes.enums import DirectlyStatus
from pneumatic_backend.accounts.enums import (
    NotificationType,
)
from pneumatic_backend.accounts.models import Notification
from pneumatic_backend.processes.models import TaskPerformer
from pneumatic_backend.notifications.enums import (
    NotificationMethod,
)


pytestmark = pytest.mark.django_db


def test_send_urgent_notification__call_services__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(account_owner)
    websocket_urgent_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_urgent'
    )
    websocket_not_urgent_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_not_urgent'
    )

    # act
    _send_urgent_notification(
        author_id=user.id,
        task_id=task.id,
        account_id=account.id,
        notification_type=NotificationType.URGENT,
        method_name=NotificationMethod.urgent
    )

    # assert
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=account_owner.id,
        author_id=user.id,
        account_id=account.id,
        type=NotificationType.URGENT,
        text=None
    )

    websocket_kwargs = {}
    websocket_urgent_mock.assert_called_once_with(
        user_id=account_owner.id,
        sync=True,
        notification=notification,
        **websocket_kwargs,
    )
    websocket_not_urgent_mock.assert_not_called()


def test_send_not_urgent_notification__call_services__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(account_owner)
    websocket_urgent_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_urgent'
    )
    websocket_not_urgent_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_not_urgent'
    )

    # act
    _send_urgent_notification(
        author_id=user.id,
        task_id=task.id,
        account_id=account.id,
        notification_type=NotificationType.NOT_URGENT,
        method_name=NotificationMethod.not_urgent
    )

    # assert
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=account_owner.id,
        author_id=user.id,
        account_id=account.id,
        type=NotificationType.NOT_URGENT,
        text=None
    )

    websocket_kwargs = {}
    websocket_not_urgent_mock.assert_called_once_with(
        user_id=account_owner.id,
        sync=True,
        notification=notification,
        **websocket_kwargs,
    )
    websocket_urgent_mock.assert_not_called()


def test_send_urgent_notification_completed_performer__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    TaskPerformer.objects.create(
        task=task,
        user=account_owner,
        is_completed=True,
        date_completed=timezone.now()
    )
    websocket_urgent_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_urgent'
    )
    websocket_not_urgent_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_not_urgent'
    )

    # act
    _send_urgent_notification(
        author_id=user.id,
        task_id=task.id,
        account_id=account.id,
        notification_type=NotificationType.URGENT,
        method_name=NotificationMethod.urgent
    )

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=account_owner.id,
        author_id=user.id,
        account_id=account.id,
        type=NotificationType.URGENT,
        text=None
    ).exists()

    websocket_urgent_mock.assert_not_called()
    websocket_not_urgent_mock.assert_not_called()


def test_send_urgent_notification_deleted_performer__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    TaskPerformer.objects.create(
        task=task,
        user=account_owner,
        is_completed=False,
        directly_status=DirectlyStatus.DELETED,
        date_completed=timezone.now()
    )
    websocket_urgent_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_urgent'
    )
    websocket_not_urgent_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_not_urgent'
    )

    # act
    _send_urgent_notification(
        author_id=user.id,
        task_id=task.id,
        account_id=account.id,
        notification_type=NotificationType.URGENT,
        method_name=NotificationMethod.urgent
    )

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=account_owner.id,
        author_id=user.id,
        account_id=account.id,
        type=NotificationType.URGENT,
        text=None
    ).exists()

    websocket_urgent_mock.assert_not_called()
    websocket_not_urgent_mock.assert_not_called()


def test_send_urgent_notification_guest_performer__skip(mocker):

    # arrange
    account = create_test_account()
    create_test_user(
        is_account_owner=True,
        account=account
    )
    user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False
    )
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    TaskPerformer.objects.create(
        task=task,
        user=guest,
    )
    websocket_urgent_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_urgent'
    )
    websocket_not_urgent_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_not_urgent'
    )

    # act
    _send_urgent_notification(
        author_id=user.id,
        task_id=task.id,
        account_id=account.id,
        notification_type=NotificationType.URGENT,
        method_name=NotificationMethod.urgent
    )

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=guest.id,
        author_id=user.id,
        account_id=account.id,
        type=NotificationType.URGENT,
        text=None
    ).exists()

    websocket_urgent_mock.assert_not_called()
    websocket_not_urgent_mock.assert_not_called()


def test_send_urgent_notification__another_task__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False
    )
    workflow = create_test_workflow(user, tasks_count=2)
    task_1 = workflow.tasks.get(number=1)
    task_1.date_completed = timezone.now()
    task_1.is_completed = True
    task_1.save()
    task_1.performers.add(account_owner)

    workflow.current_task = 2
    workflow.save()
    task_2 = workflow.tasks.get(number=2)
    task_2.performers.add(account_owner)

    websocket_urgent_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_urgent'
    )
    websocket_not_urgent_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_not_urgent'
    )

    # act
    _send_urgent_notification(
        author_id=user.id,
        task_id=task_2.id,
        account_id=account.id,
        notification_type=NotificationType.URGENT,
        method_name=NotificationMethod.urgent
    )

    # assert
    notification = Notification.objects.get(
        task_id=task_2.id,
        user_id=account_owner.id,
        author_id=user.id,
        account_id=account.id,
        type=NotificationType.URGENT,
        text=None
    )

    websocket_kwargs = {}
    websocket_urgent_mock.assert_called_once_with(
        user_id=account_owner.id,
        sync=True,
        notification=notification,
        **websocket_kwargs,
    )
    websocket_not_urgent_mock.assert_not_called()
