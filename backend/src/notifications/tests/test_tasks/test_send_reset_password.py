import pytest
from django.conf import settings

from src.notifications.enums import (
    NotificationMethod,
)
from src.notifications.services.email import (
    EmailService,
)
from src.notifications.tasks import (
    _send_reset_password_notification,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_user,
)

pytestmark = pytest.mark.django_db


def test_send_reset_password_notification__call_all_services__ok(mocker):

    # arrange
    account = create_test_account(
        logo_lg='https://best.com/logo.jpg',
        log_api_requests=True,
    )
    email = 'man@best.com'
    user = create_test_user(account=account, email=email)
    email_service_init_mock = mocker.patch.object(
        EmailService,
        attribute='__init__',
        return_value=None,
    )
    token = 'some_token'
    get_token_mock = mocker.patch(
        'src.accounts.tokens.ResetPasswordToken.for_user_id',
        return_value=token,
    )
    email_service_mock = mocker.patch(
        'src.notifications.services.email.EmailService.send_reset_password',
    )

    # act
    _send_reset_password_notification(
        logging=account.log_api_requests,
        user_id=user.id,
        user_email=email,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )

    # assert
    get_token_mock.assert_called_once_with(user.id)
    email_service_init_mock.assert_called_once_with(
        logo_lg=account.logo_lg,
        account_id=account.id,
        logging=account.log_api_requests,
    )
    email_service_mock.assert_called_once_with(
        link=f'{settings.FRONTEND_URL}/auth/reset-password/?token={token}',
        token=token,
        user_id=user.id,
        user_email=email,
        sync=True,
    )


def test_send_reset_password_notification__ok(mocker):

    # arrange
    logo = 'https://best.com/logo.jpg'
    email = 'man@best.com'
    account = create_test_account(logo_lg=logo)
    user = create_test_user(account=account, email=email)
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )
    token = 'some_token'
    get_token_mock = mocker.patch(
        'src.accounts.tokens.ResetPasswordToken.for_user_id',
        return_value=token,
    )

    # act
    _send_reset_password_notification(
        logging=account.log_api_requests,
        user_id=user.id,
        user_email=email,
        logo_lg=logo,
        account_id=account.id,
    )

    # assert
    get_token_mock.assert_called_once_with(user.id)
    send_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        method_name=NotificationMethod.reset_password,
        user_id=user.id,
        user_email=email,
        logo_lg=logo,
        account_id=account.id,
        link=f'{settings.FRONTEND_URL}/auth/reset-password/?token={token}',
        token=token,
        sync=True,
    )
