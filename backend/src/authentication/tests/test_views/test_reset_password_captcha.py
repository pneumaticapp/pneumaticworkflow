import pytest
from drf_recaptcha.validators import ReCaptchaV2Validator

from src.processes.tests.fixtures import (
    create_test_user,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_captcha__first_request__not_show(api_client, mocker):

    # arrange
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=False,
    )
    settings_mock = mocker.patch(
        'src.authentication.views.password.settings',
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.get('/auth/reset-password/captcha')

    # assert
    assert response.status_code == 200
    assert response.data['show_captcha'] is False
    assert anonymous_user_reset_exists_mock.call_count == 1


def test_captcha__second_request__show(api_client, mocker):

    # arrange
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=True,
    )
    settings_mock = mocker.patch(
        'src.authentication.views.password.settings',
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.get('/auth/reset-password/captcha')

    # assert
    assert response.status_code == 200
    assert response.data['show_captcha'] is True
    assert anonymous_user_reset_exists_mock.call_count == 1


def test_captcha__ip_not_found__show(api_client, mocker):

    # arrange
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=None,
    )
    settings_mock = mocker.patch(
        'src.authentication.views.password.settings',
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.get('/auth/reset-password/captcha')

    # assert
    assert response.status_code == 200
    assert response.data['show_captcha'] is True
    assert anonymous_user_reset_exists_mock.call_count == 1


def test_captcha__disabled__not_show(api_client, mocker):

    # arrange
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=True,
    )
    settings_mock = mocker.patch(
        'src.authentication.views.password.settings',
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': False}

    # act
    response = api_client.get('/auth/reset-password/captcha')

    # assert
    assert response.status_code == 200
    assert response.data['show_captcha'] is False
    anonymous_user_reset_exists_mock.assert_not_called()


def test_create__first_request__ok_without_captcha(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
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
    settings_mock = mocker.patch(
        'src.authentication.views.password.settings',
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.post(
        '/auth/reset-password',
        data={'email': user.email},
    )

    # assert
    assert response.status_code == 204
    assert anonymous_user_reset_exists_mock.call_count == 1
    assert inc_anonymous_user_reset_counter_mock.call_count == 1
    send_reset_password_notification_mock.assert_called_once_with(
        user_id=user.id,
        user_email=user.email,
        logo_lg=user.account.logo_lg,
        logging=user.account.log_api_requests,
        account_id=user.account_id,
    )


def test_create__second_request_with_captcha__ok(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=True,
    )
    inc_anonymous_user_reset_counter_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.inc_anonymous_user_reset_counter',
    )
    send_reset_password_notification_mock = mocker.patch(
        'src.authentication.views.password.'
        'send_reset_password_notification.delay',
    )
    mocker.patch.object(
        ReCaptchaV2Validator,
        attribute='__call__',
    )
    settings_mock = mocker.patch(
        'src.authentication.views.password.settings',
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.post(
        '/auth/reset-password',
        data={
            'email': user.email,
            'captcha': 'skip',
        },
    )

    # assert
    assert response.status_code == 204
    assert anonymous_user_reset_exists_mock.call_count == 1
    assert inc_anonymous_user_reset_counter_mock.call_count == 1
    send_reset_password_notification_mock.assert_called_once_with(
        user_id=user.id,
        user_email=user.email,
        logo_lg=user.account.logo_lg,
        logging=user.account.log_api_requests,
        account_id=user.account_id,
    )


def test_create__second_request_without_captcha__error(
    api_client,
    mocker,
):

    # arrange
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=True,
    )
    inc_anonymous_user_reset_counter_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.inc_anonymous_user_reset_counter',
    )
    send_reset_password_notification_mock = mocker.patch(
        'src.authentication.views.password.'
        'send_reset_password_notification.delay',
    )
    settings_mock = mocker.patch(
        'src.authentication.views.password.settings',
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': True}

    # act
    response = api_client.post(
        '/auth/reset-password',
        data={'email': 'test@pneumatic.app'},
    )

    # assert
    message = 'This field is required.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'captcha'
    assert response.data['details']['reason'] == message
    assert anonymous_user_reset_exists_mock.call_count == 1
    assert inc_anonymous_user_reset_counter_mock.call_count == 1
    send_reset_password_notification_mock.assert_not_called()


def test_create__captcha_disabled__ok_without_captcha(
    api_client,
    mocker,
):

    # arrange
    user = create_test_user()
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=True,
    )
    inc_anonymous_user_reset_counter_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.inc_anonymous_user_reset_counter',
    )
    send_reset_password_notification_mock = mocker.patch(
        'src.authentication.views.password.'
        'send_reset_password_notification.delay',
    )
    settings_mock = mocker.patch(
        'src.authentication.views.password.settings',
    )
    settings_mock.PROJECT_CONF = {'CAPTCHA': False}

    # act
    response = api_client.post(
        '/auth/reset-password',
        data={'email': user.email},
    )

    # assert
    assert response.status_code == 204
    assert anonymous_user_reset_exists_mock.call_count == 1
    assert inc_anonymous_user_reset_counter_mock.call_count == 1
    send_reset_password_notification_mock.assert_called_once_with(
        user_id=user.id,
        user_email=user.email,
        logo_lg=user.account.logo_lg,
        logging=user.account.log_api_requests,
        account_id=user.account_id,
    )
