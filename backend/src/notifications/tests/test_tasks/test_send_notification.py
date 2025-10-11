import pytest
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_guest,
    create_test_account,
)
from src.notifications.enums import NotificationMethod
from src.notifications.tasks import _send_notification
from src.notifications.services.email import (
    EmailService,
)
from src.notifications.services.websockets import (
    WebSocketService,
)
from src.notifications.services.push import (
    PushNotificationService,
)


pytestmark = pytest.mark.django_db


def test_send_notification__user__ok(mocker):

    # arrange
    account = create_test_account(
        logo_lg='https://logo.jpg',
        log_api_requests=True,
    )
    user = create_test_user(account=account)
    method_name = NotificationMethod.overdue_task
    kwargs = {'some': 'data'}
    email_service_init_mock = mocker.patch.object(
        EmailService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.notifications.services.email.'
        'EmailService.ALLOWED_METHODS',
        {NotificationMethod.overdue_task},
    )
    email_notification_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService.send_overdue_task',
    )
    mocker.patch(
        'src.notifications.services.push.'
        'PushNotificationService.ALLOWED_METHODS',
        {NotificationMethod.overdue_task},
    )
    push_notification_service_init_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None,
    )
    push_notification_mock = mocker.patch(
        'src.notifications.services.push.'
        'PushNotificationService.send_overdue_task',
    )
    websocket_service_init_mock = mocker.patch.object(
        WebSocketService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.ALLOWED_METHODS',
        {NotificationMethod.overdue_task},
    )
    websocket_notification_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_overdue_task',
    )

    # act
    _send_notification(
        logging=account.log_api_requests,
        method_name=method_name,
        user_id=user.id,
        user_email=user.email,
        account_id=account.id,
        logo_lg=account.logo_lg,
        **kwargs,
    )

    # assert
    email_service_init_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    email_notification_mock.assert_called_once_with(
        user_id=user.id,
        user_email=user.email,
        **kwargs,
    )
    push_notification_service_init_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    push_notification_mock.assert_called_once_with(
        user_id=user.id,
        user_email=user.email,
        **kwargs,
    )
    websocket_service_init_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    websocket_notification_mock.assert_called_once_with(
        user_id=user.id,
        user_email=user.email,
        **kwargs,
    )


def test_send_notification__guest__ok(mocker):

    # arrange
    account = create_test_account(
        logo_lg='https://logo.jpg',
        log_api_requests=True,
    )
    create_test_user(account=account)
    guest = create_test_guest(account=account)
    method_name = NotificationMethod.overdue_task
    kwargs = {'some': 'data'}
    email_service_init_mock = mocker.patch.object(
        EmailService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.notifications.services.email.'
        'EmailService.ALLOWED_METHODS',
        {NotificationMethod.overdue_task},
    )
    email_notification_mock = mocker.patch(
        'src.notifications.services.email.'
        'EmailService.send_overdue_task',
    )
    mocker.patch(
        'src.notifications.services.push.'
        'PushNotificationService.ALLOWED_METHODS',
        {NotificationMethod.overdue_task},
    )
    push_notification_service_init_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None,
    )
    push_notification_mock = mocker.patch(
        'src.notifications.services.push.'
        'PushNotificationService.send_overdue_task',
    )
    websocket_service_init_mock = mocker.patch.object(
        WebSocketService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.ALLOWED_METHODS',
        {NotificationMethod.overdue_task},
    )
    websocket_notification_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_overdue_task',
    )

    # act
    _send_notification(
        logging=account.log_api_requests,
        method_name=method_name,
        user_id=guest.id,
        user_email=guest.email,
        account_id=account.id,
        logo_lg=account.logo_lg,
        **kwargs,
    )

    # assert
    email_service_init_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    email_notification_mock.assert_called_once_with(
        user_id=guest.id,
        user_email=guest.email,
        **kwargs,
    )
    push_notification_service_init_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    push_notification_mock.assert_called_once_with(
        user_id=guest.id,
        user_email=guest.email,
        **kwargs,
    )
    websocket_service_init_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    websocket_notification_mock.assert_called_once_with(
        user_id=guest.id,
        user_email=guest.email,
        **kwargs,
    )
