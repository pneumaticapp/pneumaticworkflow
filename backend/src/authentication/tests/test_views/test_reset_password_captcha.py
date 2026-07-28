import pytest
from unittest.mock import ANY

from django.conf import settings
from drf_recaptcha.validators import ReCaptchaV2Validator

from src.processes.tests.fixtures import (
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_captcha__first_request__not_show(api_client, mocker):

    """ First reset request, captcha enabled — hide """

    # arrange
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=False,
    )
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'CAPTCHA': True},
    )

    # act
    response = api_client.get('/auth/reset-password/captcha')

    # assert
    assert response.status_code == 200
    assert response.data['show_captcha'] is False
    anonymous_user_reset_exists_mock.assert_called_once_with(ANY)


def test_captcha__second_request__show(api_client, mocker):

    """ Repeated reset request — show captcha """

    # arrange
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=True,
    )
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'CAPTCHA': True},
    )

    # act
    response = api_client.get('/auth/reset-password/captcha')

    # assert
    assert response.status_code == 200
    assert response.data['show_captcha'] is True
    anonymous_user_reset_exists_mock.assert_called_once_with(ANY)


def test_captcha__ip_not_found__show(api_client, mocker):

    """ IP not in request headers — show captcha """

    # arrange
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=None,
    )
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'CAPTCHA': True},
    )

    # act
    response = api_client.get('/auth/reset-password/captcha')

    # assert
    assert response.status_code == 200
    assert response.data['show_captcha'] is True
    anonymous_user_reset_exists_mock.assert_called_once_with(ANY)


def test_captcha__disabled__not_show(api_client, mocker):

    """ Captcha disabled in settings — hide """

    # arrange
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=True,
    )
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'CAPTCHA': False},
    )

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

    """ First reset request — captcha not required """

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
    send_reset_pwd_notification_mock = mocker.patch(
        'src.authentication.views.password.'
        'send_reset_password_notification.delay',
    )
    check_sso_restrictions_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.check_sso_restrictions',
    )
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'CAPTCHA': True},
    )

    # act
    response = api_client.post(
        '/auth/reset-password',
        data={'email': user.email},
    )

    # assert
    assert response.status_code == 204
    anonymous_user_reset_exists_mock.assert_called_once_with(ANY)
    inc_anonymous_user_reset_counter_mock.assert_called_once_with(
        ANY,
    )
    send_reset_pwd_notification_mock.assert_called_once_with(
        user_id=user.id,
        user_email=user.email,
        logo_lg=user.account.logo_lg,
        logging=user.account.log_api_requests,
        account_id=user.account_id,
    )
    check_sso_restrictions_mock.assert_called_once_with(user)


def test_create__second_request_with_captcha__ok(
    api_client,
    mocker,
):

    """ Repeated request with valid captcha — ok """

    # arrange
    user = create_test_owner()
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=True,
    )
    inc_anonymous_user_reset_counter_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.inc_anonymous_user_reset_counter',
    )
    send_reset_pwd_notification_mock = mocker.patch(
        'src.authentication.views.password.'
        'send_reset_password_notification.delay',
    )
    check_sso_restrictions_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.check_sso_restrictions',
    )
    recaptcha_v2_validator_call_mock = mocker.patch.object(
        ReCaptchaV2Validator,
        attribute='__call__',
    )
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'CAPTCHA': True},
    )

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
    anonymous_user_reset_exists_mock.assert_called_once_with(ANY)
    inc_anonymous_user_reset_counter_mock.assert_called_once_with(
        ANY,
    )
    send_reset_pwd_notification_mock.assert_called_once_with(
        user_id=user.id,
        user_email=user.email,
        logo_lg=user.account.logo_lg,
        logging=user.account.log_api_requests,
        account_id=user.account_id,
    )
    check_sso_restrictions_mock.assert_called_once_with(user)
    assert recaptcha_v2_validator_call_mock.call_count == 1


def test_create__captcha_disabled__ok_without_captcha(
    api_client,
    mocker,
):

    """ Captcha disabled — ok without captcha """

    # arrange
    user = create_test_owner()
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=True,
    )
    inc_anonymous_user_reset_counter_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.inc_anonymous_user_reset_counter',
    )
    send_reset_pwd_notification_mock = mocker.patch(
        'src.authentication.views.password.'
        'send_reset_password_notification.delay',
    )
    check_sso_restrictions_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.check_sso_restrictions',
    )
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'CAPTCHA': False},
    )

    # act
    response = api_client.post(
        '/auth/reset-password',
        data={'email': user.email},
    )

    # assert
    assert response.status_code == 204
    anonymous_user_reset_exists_mock.assert_called_once_with(ANY)
    inc_anonymous_user_reset_counter_mock.assert_called_once_with(
        ANY,
    )
    send_reset_pwd_notification_mock.assert_called_once_with(
        user_id=user.id,
        user_email=user.email,
        logo_lg=user.account.logo_lg,
        logging=user.account.log_api_requests,
        account_id=user.account_id,
    )
    check_sso_restrictions_mock.assert_called_once_with(user)


def test_create__user_not_found__ok_no_notification(
    api_client,
    mocker,
):

    """ Email not in DB — 204, no notification sent """

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
    send_reset_pwd_notification_mock = mocker.patch(
        'src.authentication.views.password.'
        'send_reset_password_notification.delay',
    )
    check_sso_restrictions_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.check_sso_restrictions',
    )
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'CAPTCHA': True},
    )

    # act
    response = api_client.post(
        '/auth/reset-password',
        data={'email': 'nonexistent@pneumatic.app'},
    )

    # assert
    assert response.status_code == 204
    anonymous_user_reset_exists_mock.assert_called_once_with(ANY)
    inc_anonymous_user_reset_counter_mock.assert_called_once_with(
        ANY,
    )
    send_reset_pwd_notification_mock.assert_not_called()
    check_sso_restrictions_mock.assert_not_called()


def test_create__second_request_no_captcha__validation_err(
    api_client,
    mocker,
):

    """ Repeated request without captcha — validation error """

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
    send_reset_pwd_notification_mock = mocker.patch(
        'src.authentication.views.password.'
        'send_reset_password_notification.delay',
    )
    check_sso_restrictions_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.check_sso_restrictions',
    )
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'CAPTCHA': True},
    )

    # act
    response = api_client.post(
        '/auth/reset-password',
        data={'email': 'test@pneumatic.app'},
    )

    # assert

    # DRF built-in required field validation message
    message = 'This field is required.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'captcha'
    assert response.data['details']['reason'] == message
    anonymous_user_reset_exists_mock.assert_called_once_with(ANY)
    inc_anonymous_user_reset_counter_mock.assert_called_once_with(
        ANY,
    )
    send_reset_pwd_notification_mock.assert_not_called()
    check_sso_restrictions_mock.assert_not_called()


def test_create__ip_not_found_no_captcha__validation_err(
    api_client,
    mocker,
):

    """ IP not found, no captcha sent — validation error """

    # arrange
    anonymous_user_reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=None,
    )
    inc_anonymous_user_reset_counter_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.inc_anonymous_user_reset_counter',
    )
    send_reset_pwd_notification_mock = mocker.patch(
        'src.authentication.views.password.'
        'send_reset_password_notification.delay',
    )
    check_sso_restrictions_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.check_sso_restrictions',
    )
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'CAPTCHA': True},
    )

    # act
    response = api_client.post(
        '/auth/reset-password',
        data={'email': 'test@pneumatic.app'},
    )

    # assert

    # DRF built-in required field validation message
    message = 'This field is required.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'captcha'
    assert response.data['details']['reason'] == message
    anonymous_user_reset_exists_mock.assert_called_once_with(ANY)
    inc_anonymous_user_reset_counter_mock.assert_called_once_with(
        ANY,
    )
    send_reset_pwd_notification_mock.assert_not_called()
    check_sso_restrictions_mock.assert_not_called()
