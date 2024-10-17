import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
)
from pneumatic_backend.notifications.tasks import (
    _send_reset_password_notification
)
from pneumatic_backend.notifications.enums import (
    NotificationMethod,
)


pytestmark = pytest.mark.django_db


def test_send_reset_password_notification__call_services(mocker):

    # arrange
    logo = 'https://best.com/logo.jpg'
    email = 'man@best.com'
    account = create_test_account(logo_lg=logo)
    user = create_test_user(account=account, email=email)
    email_service_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService.send_reset_password'
    )

    # act
    _send_reset_password_notification(
        user_id=user.id,
        user_email=email,
        logo_lg=logo
    )
    email_kwargs = {
        'sync': True
    }

    # assert
    email_service_mock.assert_called_once_with(
        user_id=user.id,
        user_email=email,
        logo_lg=logo,
        **email_kwargs
    )


def test_send_reset_password_notification__ok(mocker):

    # arrange
    logo = 'https://best.com/logo.jpg'
    email = 'man@best.com'
    account = create_test_account(logo_lg=logo)
    user = create_test_user(account=account, email=email)
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )

    # act
    _send_reset_password_notification(
        user_id=user.id,
        user_email=email,
        logo_lg=logo
    )

    # assert
    send_notification_mock.assert_called_once_with(
        method_name=NotificationMethod.reset_password,
        user_id=user.id,
        user_email=email,
        logo_lg=logo,
        sync=True
    )
