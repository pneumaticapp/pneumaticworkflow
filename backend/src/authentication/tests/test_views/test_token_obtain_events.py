from datetime import timedelta

import pytest

from src.accounts.enums import SourceType
from src.authentication.enums import AuthTokenType
from src.authentication.messages import (
    MSG_AU_0002,
    MSG_AU_0003,
    MSG_AU_0016,
)
from src.logs.events.enums import LoginFailedReason
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_signin__valid_credentials__audit_user_logged_in(
    mocker,
    api_client,
    identify_mock,
):

    # arrange
    user = create_test_owner()
    user.set_password('12345')
    user.save(update_fields=['password'])
    users_logged_in_mock = mocker.patch(
        'src.authentication.views.signin.'
        'AnalyticService.users_logged_in',
    )
    user_logged_in_mock = mocker.patch(
        'src.authentication.views.signin.AuditEventService.user_logged_in',
    )
    login_failed_mock = mocker.patch(
        'src.authentication.views.signin.AuditEventService.login_failed',
    )

    # act
    response = api_client.post(
        path='/auth/token/obtain',
        data={
            'username': user.email,
            'password': '12345',
        },
    )

    # assert
    assert response.status_code == 200
    user_logged_in_mock.assert_called_once_with(
        user=user,
        source=SourceType.EMAIL,
    )
    login_failed_mock.assert_not_called()
    identify_mock.assert_called_once_with(user)
    users_logged_in_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        source=SourceType.EMAIL,
    )


def test_signin__wrong_password__audit_login_failed(
    mocker,
    api_client,
    identify_mock,
):

    # arrange
    user = create_test_owner()
    user.set_password('12345')
    user.save(update_fields=['password'])
    users_logged_in_mock = mocker.patch(
        'src.authentication.views.signin.'
        'AnalyticService.users_logged_in',
    )
    user_logged_in_mock = mocker.patch(
        'src.authentication.views.signin.AuditEventService.user_logged_in',
    )
    login_failed_mock = mocker.patch(
        'src.authentication.views.signin.AuditEventService.login_failed',
    )

    # act
    response = api_client.post(
        path='/auth/token/obtain',
        data={
            'username': user.email,
            'password': 'YouShallNotPass',
        },
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_AU_0003
    login_failed_mock.assert_called_once_with(
        reason=LoginFailedReason.BAD_CREDENTIALS,
        email=user.email,
    )
    user_logged_in_mock.assert_not_called()
    identify_mock.assert_not_called()
    users_logged_in_mock.assert_not_called()


def test_signin__unknown_email__audit_login_failed_with_same_reason(
    mocker,
    api_client,
    identify_mock,
):

    # arrange
    users_logged_in_mock = mocker.patch(
        'src.authentication.views.signin.'
        'AnalyticService.users_logged_in',
    )
    user_logged_in_mock = mocker.patch(
        'src.authentication.views.signin.AuditEventService.user_logged_in',
    )
    login_failed_mock = mocker.patch(
        'src.authentication.views.signin.AuditEventService.login_failed',
    )

    # act
    response = api_client.post(
        path='/auth/token/obtain',
        data={
            'username': 'ghost@pneumatic.app',
            'password': '12345',
        },
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_AU_0003
    login_failed_mock.assert_called_once_with(
        reason=LoginFailedReason.BAD_CREDENTIALS,
        email='ghost@pneumatic.app',
    )
    user_logged_in_mock.assert_not_called()
    identify_mock.assert_not_called()
    users_logged_in_mock.assert_not_called()


def test_signin__sso_required__audit_login_failed_sso_required(
    mocker,
    api_client,
    identify_mock,
    settings,
):

    # arrange
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SSO_AUTH': True}
    user = create_test_admin()
    user.set_password('12345')
    user.save(update_fields=['password'])
    users_logged_in_mock = mocker.patch(
        'src.authentication.views.signin.'
        'AnalyticService.users_logged_in',
    )
    user_logged_in_mock = mocker.patch(
        'src.authentication.views.signin.AuditEventService.user_logged_in',
    )
    login_failed_mock = mocker.patch(
        'src.authentication.views.signin.AuditEventService.login_failed',
    )

    # act
    response = api_client.post(
        path='/auth/token/obtain',
        data={
            'username': user.email,
            'password': '12345',
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data[0] == MSG_AU_0016
    login_failed_mock.assert_called_once_with(
        reason=LoginFailedReason.SSO_REQUIRED,
        email=user.email,
    )
    user_logged_in_mock.assert_not_called()
    identify_mock.assert_not_called()
    users_logged_in_mock.assert_not_called()


def test_signin__verification_timed_out__audit_login_failed_expired(
    mocker,
    api_client,
    identify_mock,
    verification_check_true_mock,
):

    # arrange
    user = create_test_owner()
    user.set_password('12345')
    user.save(update_fields=['password'])
    account = user.account
    account.is_verified = False
    account.date_joined = user.date_joined - timedelta(weeks=3)
    account.save(update_fields=['is_verified', 'date_joined'])
    send_verification_mock = mocker.patch(
        'src.authentication.views.signin.'
        'send_verification_notification.delay',
    )
    user_logged_in_mock = mocker.patch(
        'src.authentication.views.signin.AuditEventService.user_logged_in',
    )
    login_failed_mock = mocker.patch(
        'src.authentication.views.signin.AuditEventService.login_failed',
    )

    # act
    response = api_client.post(
        path='/auth/token/obtain',
        data={
            'username': user.email,
            'password': '12345',
        },
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_AU_0002(user.email)
    login_failed_mock.assert_called_once_with(
        reason=LoginFailedReason.VERIFICATION_EXPIRED,
        email=user.email,
    )
    user_logged_in_mock.assert_not_called()
    identify_mock.assert_not_called()
    send_verification_mock.assert_called_once_with(
        user_id=user.id,
        user_email=user.email,
        account_id=user.account_id,
        user_first_name=user.first_name,
        token=mocker.ANY,
        logo_lg=account.logo_lg,
    )
