import pytest
from rest_framework_simplejwt.exceptions import TokenError

from src.accounts.tokens import ResetPasswordToken
from src.authentication.enums import AuthTokenType
from src.authentication.messages import MSG_AU_0012, MSG_AU_0016
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_reset_password__known_address__audit_reset_requested(
    mocker,
    api_client,
):

    # arrange
    user = create_test_owner()
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=False,
    )
    inc_anonymous_user_reset_counter_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.inc_anonymous_user_reset_counter',
    )
    send_reset_password_notification_mock = mocker.patch(
        'src.authentication.views.password.'
        'send_reset_password_notification.delay',
    )
    password_reset_requested_mock = mocker.patch(
        'src.authentication.views.password.AuditEventService.'
        'password_reset_requested',
    )

    # act
    response = api_client.post(
        '/auth/reset-password',
        {'email': user.email},
    )

    # assert
    assert response.status_code == 204
    password_reset_requested_mock.assert_called_once_with(target=user)
    anonymous_user_reset_exists_mock.assert_called_once_with(mocker.ANY)
    inc_anonymous_user_reset_counter_mock.assert_called_once_with(mocker.ANY)
    send_reset_password_notification_mock.assert_called_once_with(
        user_id=user.id,
        user_email=user.email,
        logo_lg=user.account.logo_lg,
        logging=user.account.log_api_requests,
        account_id=user.account_id,
    )


def test_reset_password__unknown_address__audit_not_called(
    mocker,
    api_client,
):

    """ No e-mail goes out for an address nobody has, so nothing
        happened in any account. """

    # arrange
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=False,
    )
    inc_anonymous_user_reset_counter_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.inc_anonymous_user_reset_counter',
    )
    send_reset_password_notification_mock = mocker.patch(
        'src.authentication.views.password.'
        'send_reset_password_notification.delay',
    )
    password_reset_requested_mock = mocker.patch(
        'src.authentication.views.password.AuditEventService.'
        'password_reset_requested',
    )

    # act
    response = api_client.post(
        '/auth/reset-password',
        {'email': 'nobody@test.test'},
    )

    # assert
    assert response.status_code == 204
    password_reset_requested_mock.assert_not_called()
    anonymous_user_reset_exists_mock.assert_called_once_with(mocker.ANY)
    inc_anonymous_user_reset_counter_mock.assert_called_once_with(mocker.ANY)
    send_reset_password_notification_mock.assert_not_called()


def test_reset_password__sso_restricted__audit_not_called(
    mocker,
    api_client,
    settings,
):

    # arrange
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SSO_AUTH': True}
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=False,
    )
    inc_anonymous_user_reset_counter_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.inc_anonymous_user_reset_counter',
    )
    send_reset_password_notification_mock = mocker.patch(
        'src.authentication.views.password.'
        'send_reset_password_notification.delay',
    )
    password_reset_requested_mock = mocker.patch(
        'src.authentication.views.password.AuditEventService.'
        'password_reset_requested',
    )

    # act
    response = api_client.post(
        '/auth/reset-password',
        {'email': user.email},
    )

    # assert
    assert response.status_code == 400
    assert response.data[0] == MSG_AU_0016
    password_reset_requested_mock.assert_not_called()
    anonymous_user_reset_exists_mock.assert_called_once_with(mocker.ANY)
    inc_anonymous_user_reset_counter_mock.assert_called_once_with(mocker.ANY)
    send_reset_password_notification_mock.assert_not_called()


def test_confirm__valid_token__audit_password_reset(
    mocker,
    api_client,
    expire_tokens_mock,
):

    # arrange
    user = create_test_owner()
    change_password_mock = mocker.patch(
        'src.accounts.services.user.UserService.change_password',
    )
    password_reset_mock = mocker.patch(
        'src.authentication.views.password.AuditEventService.'
        'password_reset',
    )
    data = {
        'new_password': 'new-pass-1',
        'confirm_new_password': 'new-pass-1',
        'token': str(ResetPasswordToken.for_user(user)),
    }

    # act
    response = api_client.post('/auth/reset-password/confirm', data)

    # assert
    assert response.status_code == 200
    password_reset_mock.assert_called_once_with(user=user)
    change_password_mock.assert_called_once_with(password='new-pass-1')
    expire_tokens_mock.assert_called_once_with(user)


def test_confirm__invalid_token__audit_not_called(
    mocker,
    api_client,
    expire_tokens_mock,
):

    # arrange
    change_password_mock = mocker.patch(
        'src.accounts.services.user.UserService.change_password',
    )
    password_reset_mock = mocker.patch(
        'src.authentication.views.password.AuditEventService.'
        'password_reset',
    )
    data = {
        'new_password': 'new-pass-1',
        'confirm_new_password': 'new-pass-1',
        'token': 'not-a-token',
    }

    # act
    with pytest.raises(TokenError):
        api_client.post('/auth/reset-password/confirm', data)

    # assert
    password_reset_mock.assert_not_called()
    change_password_mock.assert_not_called()
    expire_tokens_mock.assert_not_called()


def test_confirm__sso_restricted__audit_not_called(
    mocker,
    api_client,
    expire_tokens_mock,
    settings,
):

    # arrange
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SSO_AUTH': True}
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    change_password_mock = mocker.patch(
        'src.accounts.services.user.UserService.change_password',
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.'
        'AuthService.get_auth_token',
    )
    password_reset_mock = mocker.patch(
        'src.authentication.views.password.AuditEventService.'
        'password_reset',
    )
    data = {
        'new_password': 'new-pass-1',
        'confirm_new_password': 'new-pass-1',
        'token': str(ResetPasswordToken.for_user(user)),
    }

    # act
    response = api_client.post('/auth/reset-password/confirm', data)

    # assert
    assert response.status_code == 400
    assert response.data[0] == MSG_AU_0016
    password_reset_mock.assert_not_called()
    change_password_mock.assert_not_called()
    expire_tokens_mock.assert_not_called()
    get_auth_token_mock.assert_not_called()


def test_change_password__authenticated__audit_password_changed(
    mocker,
    api_client,
    expire_tokens_mock,
):

    # arrange
    user = create_test_owner()
    user.set_password('12345')
    user.save()
    change_password_mock = mocker.patch(
        'src.accounts.services.user.UserService.change_password',
    )
    password_changed_mock = mocker.patch(
        'src.authentication.views.password.AuditEventService.'
        'password_changed',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/auth/change-password',
        data={
            'old_password': '12345',
            'new_password': '54321',
            'confirm_new_password': '54321',
        },
    )

    # assert
    assert response.status_code == 200
    password_changed_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
    )
    change_password_mock.assert_called_once_with(password='54321')
    expire_tokens_mock.assert_called_once_with(user)


def test_change_password__wrong_old_password__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    user = create_test_owner()
    user.set_password('12345')
    user.save()
    change_password_mock = mocker.patch(
        'src.accounts.services.user.UserService.change_password',
    )
    password_changed_mock = mocker.patch(
        'src.authentication.views.password.AuditEventService.'
        'password_changed',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/auth/change-password',
        data={
            'old_password': 'wrong',
            'new_password': '54321',
            'confirm_new_password': '54321',
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == str(MSG_AU_0012)
    assert response.data['details']['name'] == 'old_password'
    assert response.data['details']['reason'] == str(MSG_AU_0012)
    password_changed_mock.assert_not_called()
    change_password_mock.assert_not_called()


def test_change_password__sso_restricted__audit_not_called(
    mocker,
    api_client,
    expire_tokens_mock,
    settings,
):

    # arrange
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SSO_AUTH': True}
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    user.set_password('12345')
    user.save()
    change_password_mock = mocker.patch(
        'src.accounts.services.user.UserService.change_password',
    )
    password_changed_mock = mocker.patch(
        'src.authentication.views.password.AuditEventService.'
        'password_changed',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/auth/change-password',
        data={
            'old_password': '12345',
            'new_password': '54321',
            'confirm_new_password': '54321',
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data[0] == MSG_AU_0016
    password_changed_mock.assert_not_called()
    change_password_mock.assert_not_called()
    expire_tokens_mock.assert_not_called()
