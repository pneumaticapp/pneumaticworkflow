import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_guest,
)
from pneumatic_backend.notifications.enums import NotificationMethod
from pneumatic_backend.notifications.tasks import _send_notification

pytestmark = pytest.mark.django_db


def test_send_notification__user__ok(mocker):

    # arrange
    user = create_test_user()
    method_name = NotificationMethod.overdue_task
    kwargs = {'some': 'data'}
    mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService.ALLOWED_METHODS',
        {NotificationMethod.overdue_task}
    )
    email_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService.send_overdue_task'
    )
    mocker.patch(
        'pneumatic_backend.notifications.services.push.'
        'PushNotificationService.ALLOWED_METHODS',
        {NotificationMethod.overdue_task}
    )
    push_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.push.'
        'PushNotificationService.send_overdue_task'
    )
    mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.ALLOWED_METHODS',
        {NotificationMethod.overdue_task}
    )
    websocket_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_overdue_task'
    )

    # act
    _send_notification(
        method_name=method_name,
        user_id=user.id,
        **kwargs
    )

    # assert
    email_notification_mock.assert_called_once_with(
        user_id=user.id,
        **kwargs
    )
    push_notification_mock.assert_called_once_with(
        user_id=user.id,
        **kwargs
    )
    websocket_notification_mock.assert_called_once_with(
        user_id=user.id,
        **kwargs
    )


def test_send_notification__guest__ok(mocker):

    # arrange
    user = create_test_user()
    guest = create_test_guest(account=user.account)
    method_name = NotificationMethod.overdue_task
    kwargs = {'some': 'data'}
    mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService.ALLOWED_METHODS',
        {NotificationMethod.overdue_task}
    )
    email_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService.send_overdue_task'
    )
    mocker.patch(
        'pneumatic_backend.notifications.services.push.'
        'PushNotificationService.ALLOWED_METHODS',
        {NotificationMethod.overdue_task}
    )
    push_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.push.'
        'PushNotificationService.send_overdue_task'
    )
    mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.ALLOWED_METHODS',
        {NotificationMethod.overdue_task}
    )
    websocket_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_overdue_task'
    )

    # act
    _send_notification(
        method_name=method_name,
        user_id=guest.id,
        **kwargs
    )

    # assert
    email_notification_mock.assert_called_once_with(
        user_id=guest.id,
        **kwargs
    )
    push_notification_mock.assert_called_once_with(
        user_id=guest.id,
        **kwargs
    )
    websocket_notification_mock.assert_called_once_with(
        user_id=guest.id,
        **kwargs
    )
