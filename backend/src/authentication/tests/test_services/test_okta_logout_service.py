import pytest
import requests
from unittest.mock import Mock
from django.contrib.auth import get_user_model
from jwt import DecodeError, InvalidTokenError

from src.accounts.enums import (
    SourceType,
    UserStatus,
)
from src.authentication.models import AccessToken
from src.authentication.services.okta_logout import OktaLogoutService
from src.processes.tests.fixtures import create_test_admin
from src.utils.logging import SentryLogLevel

pytestmark = pytest.mark.django_db
user_model = get_user_model()


def test_process_logout__user_found__ok(mocker):
    # arrange
    user = create_test_admin()
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    get_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_user_by_sub',
        return_value=user,
    )
    logout_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._logout_user',
    )
    validate_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
    )
    service = OktaLogoutService(logout_token='test_token')

    sub_id_data = {
        'format': 'iss_sub',
        'iss': 'https://dev-123456.okta.com/oauth2/default',
        'sub': okta_sub,
    }
    request_data = {
        'format': 'iss_sub',
        'sub_id_data': sub_id_data,
    }

    # act
    service.process_logout(**request_data)

    # assert
    validate_mock.assert_called_once()
    get_user_mock.assert_called_once_with(okta_sub)
    logout_user_mock.assert_called_once_with(user, okta_sub=okta_sub)


def test_process_logout__user_not_found__raise_exception(mocker):
    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    get_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_user_by_sub',
        side_effect=user_model.DoesNotExist('User not found'),
    )
    logout_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._logout_user',
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
        return_value=True,
    )
    service = OktaLogoutService()

    sub_id_data = {
        'format': 'iss_sub',
        'iss': 'https://dev-123456.okta.com/oauth2/default',
        'sub': okta_sub,
    }
    request_data = {
        'format': 'iss_sub',
        'sub_id_data': sub_id_data,
    }

    # act
    service.process_logout(**request_data)

    # assert
    get_user_mock.assert_called_once_with(okta_sub)
    logout_user_mock.assert_not_called()
    capture_sentry_mock.assert_called_once()


def test_get_user_by_sub__user_found__return_user(mocker):
    # arrange
    user = create_test_admin()
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    cache_mock = Mock()
    cache_mock.get.return_value = user.id
    mocker.patch(
        'src.authentication.services.okta_logout.caches',
        {'default': cache_mock},
    )
    service = OktaLogoutService()

    # act
    result = service._get_user_by_sub(okta_sub)

    # assert
    assert result == user
    cache_mock.get.assert_called_once_with(f'okta_sub_to_user_{okta_sub}')


def test_get_user_by_sub__user_not_cached__raise_exception(mocker):
    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    cache_mock = Mock()
    cache_mock.get.return_value = None
    mocker.patch(
        'src.authentication.services.okta_logout.caches',
        {'default': cache_mock},
    )
    service = OktaLogoutService()

    # act & assert
    with pytest.raises(user_model.DoesNotExist):
        service._get_user_by_sub(okta_sub)

    cache_mock.get.assert_called_once_with(f'okta_sub_to_user_{okta_sub}')


def test_get_user_by_sub__user_not_exist__clear_cache_raise_exception(
    mocker,
):
    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    non_existent_user_id = 99999
    cache_mock = Mock()
    cache_mock.get.return_value = non_existent_user_id
    mocker.patch(
        'src.authentication.services.okta_logout.caches',
        {'default': cache_mock},
    )
    service = OktaLogoutService()

    # act & assert
    with pytest.raises(user_model.DoesNotExist):
        service._get_user_by_sub(okta_sub)

    cache_mock.get.assert_called_once_with(f'okta_sub_to_user_{okta_sub}')
    cache_mock.delete.assert_called_once_with(
        f'okta_sub_to_user_{okta_sub}',
    )


def test_logout_user__with_access_token__cleanup_all(mocker):
    # arrange
    user = create_test_admin()
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    access_token_1 = 'access_token_1'

    # Create access token (only one per user-source combination allowed)
    AccessToken.objects.create(
        user=user,
        source=SourceType.OKTA,
        access_token=access_token_1,
        refresh_token='',
        expires_in=3600,
    )

    cache_mock = Mock()
    mocker.patch(
        'src.authentication.services.okta_logout.caches',
        {'default': cache_mock},
    )
    expire_tokens_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'PneumaticToken.expire_all_tokens',
    )
    service = OktaLogoutService()

    # act
    service._logout_user(user, okta_sub=okta_sub)

    # assert
    assert AccessToken.objects.filter(
        user=user,
        source=SourceType.OKTA,
    ).count() == 0
    # Check profile cache deletion
    assert cache_mock.delete.call_count == 2
    cache_mock.delete.assert_any_call(f'user_profile_{access_token_1}')
    cache_mock.delete.assert_any_call(f'okta_sub_to_user_{okta_sub}')
    expire_tokens_mock.assert_called_once_with(user)


def test_logout_user__no_access_tokens__cleanup_minimal(mocker):
    # arrange
    user = create_test_admin()
    okta_sub = '00uid4BxXw6I6TV4m0g3'

    cache_mock = Mock()
    mocker.patch(
        'src.authentication.services.okta_logout.caches',
        {'default': cache_mock},
    )
    expire_tokens_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'PneumaticToken.expire_all_tokens',
    )
    service = OktaLogoutService()

    # act
    service._logout_user(user, okta_sub=okta_sub)

    # assert
    # Only sub cache should be cleared, no profile cache
    cache_mock.delete.assert_called_once_with(
        f'okta_sub_to_user_{okta_sub}',
    )
    expire_tokens_mock.assert_called_once_with(user)


def test_logout_user__no_okta_sub__skip_sub_cleanup(mocker):
    # arrange
    user = create_test_admin()

    cache_mock = Mock()
    mocker.patch(
        'src.authentication.services.okta_logout.caches',
        {'default': cache_mock},
    )
    expire_tokens_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'PneumaticToken.expire_all_tokens',
    )
    service = OktaLogoutService()

    # act
    service._logout_user(user, okta_sub=None)

    # assert
    # No sub cache should be cleared
    cache_mock.delete.assert_not_called()
    expire_tokens_mock.assert_called_once_with(user)


def test_validate_logout_token__valid_token__ok(mocker):
    # arrange
    logout_token = 'test_logout_token'
    domain = 'dev-123456.okta.com'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    response_data = {'active': True}
    response_mock = Mock()
    response_mock.ok = True
    response_mock.json.return_value = response_data
    request_mock = mocker.patch(
        'src.authentication.services.okta_logout.requests.post',
        return_value=response_mock,
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta_logout.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.OKTA_CLIENT_ID = client_id
    settings_mock.OKTA_CLIENT_SECRET = client_secret
    service = OktaLogoutService(logout_token=logout_token)

    # act
    result = service._validate_logout_token()

    # assert
    assert result is True
    request_mock.assert_called_once_with(
        f'https://{domain}/oauth2/default/v1/introspect',
        data={
            'token': logout_token,
            'token_type_hint': 'logout_token',
            'client_id': client_id,
            'client_secret': client_secret,
        },
        timeout=10,
    )


def test_validate_logout_token__response_not_ok__return_false(mocker):
    # arrange
    logout_token = 'test_logout_token'
    domain = 'dev-123456.okta.com'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    response_mock = Mock()
    response_mock.ok = False
    response_mock.status_code = 400
    response_mock.text = 'Bad Request'
    mocker.patch(
        'src.authentication.services.okta_logout.requests.post',
        return_value=response_mock,
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta_logout.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.OKTA_CLIENT_ID = client_id
    settings_mock.OKTA_CLIENT_SECRET = client_secret
    service = OktaLogoutService(logout_token=logout_token)

    # act
    result = service._validate_logout_token()

    # assert
    assert result is False
    capture_sentry_mock.assert_called_once_with(
        message='Okta token validation failed',
        level=SentryLogLevel.ERROR,
        data={
            'logout_token': logout_token,
            'status_code': 400,
            'response': 'Bad Request',
        },
    )


def test_validate_logout_token__token_not_active__return_false(mocker):
    # arrange
    logout_token = 'test_logout_token'
    domain = 'dev-123456.okta.com'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    response_data = {'active': False}
    response_mock = Mock()
    response_mock.ok = True
    response_mock.json.return_value = response_data
    mocker.patch(
        'src.authentication.services.okta_logout.requests.post',
        return_value=response_mock,
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta_logout.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.OKTA_CLIENT_ID = client_id
    settings_mock.OKTA_CLIENT_SECRET = client_secret
    service = OktaLogoutService(logout_token=logout_token)

    # act
    result = service._validate_logout_token()

    # assert
    assert result is False
    capture_sentry_mock.assert_called_once_with(
        message='Okta token is not active',
        level=SentryLogLevel.ERROR,
        data={
            'logout_token': logout_token,
            'result': response_data,
        },
    )


def test_validate_logout_token__jwt_decode_error__return_false(mocker):
    # arrange
    logout_token = 'test_logout_token'
    domain = 'dev-123456.okta.com'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    mocker.patch(
        'src.authentication.services.okta_logout.requests.post',
        side_effect=DecodeError('Invalid token'),
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta_logout.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.OKTA_CLIENT_ID = client_id
    settings_mock.OKTA_CLIENT_SECRET = client_secret
    service = OktaLogoutService(logout_token=logout_token)

    # act
    result = service._validate_logout_token()

    # assert
    assert result is False
    capture_sentry_mock.assert_called_once()
    assert 'Okta logout token validation failed' in (
        capture_sentry_mock.call_args[1]['message']
    )


def test_validate_logout_token__jwt_invalid_token_error__return_false(
    mocker,
):
    # arrange
    logout_token = 'test_logout_token'
    domain = 'dev-123456.okta.com'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    mocker.patch(
        'src.authentication.services.okta_logout.requests.post',
        side_effect=InvalidTokenError('Invalid token'),
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta_logout.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.OKTA_CLIENT_ID = client_id
    settings_mock.OKTA_CLIENT_SECRET = client_secret
    service = OktaLogoutService(logout_token=logout_token)

    # act
    result = service._validate_logout_token()

    # assert
    assert result is False
    capture_sentry_mock.assert_called_once()
    assert 'Okta logout token validation failed' in (
        capture_sentry_mock.call_args[1]['message']
    )


def test_validate_logout_token__request_exception__return_false(mocker):
    # arrange
    logout_token = 'test_logout_token'
    domain = 'dev-123456.okta.com'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    mocker.patch(
        'src.authentication.services.okta_logout.requests.post',
        side_effect=requests.RequestException('Connection error'),
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta_logout.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.OKTA_CLIENT_ID = client_id
    settings_mock.OKTA_CLIENT_SECRET = client_secret
    service = OktaLogoutService(logout_token=logout_token)

    # act
    result = service._validate_logout_token()

    # assert
    assert result is False
    capture_sentry_mock.assert_called_once()
    assert 'Okta logout token validation failed' in (
        capture_sentry_mock.call_args[1]['message']
    )


def test_validate_logout_token__no_token__return_false(mocker):
    # arrange
    domain = 'dev-123456.okta.com'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    response_data = {'active': False}
    response_mock = Mock()
    response_mock.ok = True
    response_mock.json.return_value = response_data
    request_mock = mocker.patch(
        'src.authentication.services.okta_logout.requests.post',
        return_value=response_mock,
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta_logout.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.OKTA_CLIENT_ID = client_id
    settings_mock.OKTA_CLIENT_SECRET = client_secret
    service = OktaLogoutService(logout_token=None)

    # act
    result = service._validate_logout_token()

    # assert
    assert result is False
    request_mock.assert_called_once()
    assert request_mock.call_args[1]['data']['token'] is None
    capture_sentry_mock.assert_called_once_with(
        message='Okta token is not active',
        level=SentryLogLevel.ERROR,
        data={
            'logout_token': None,
            'result': response_data,
        },
    )


def test_process_logout_by_email__user_found__ok(mocker):
    # arrange
    user = create_test_admin(email='test@example.com')
    email = 'test@example.com'
    logout_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._logout_user',
    )
    service = OktaLogoutService()

    # act
    service._process_logout_by_email(email)

    # assert
    logout_user_mock.assert_called_once_with(user, okta_sub=None)


def test_process_logout_by_email__user_not_found__log_sentry(mocker):
    # arrange
    email = 'nonexistent@example.com'
    logout_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._logout_user',
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    service = OktaLogoutService(logout_token='test_token')

    # act
    service._process_logout_by_email(email)

    # assert
    logout_user_mock.assert_not_called()
    capture_sentry_mock.assert_called_once_with(
        message='Okta logout: user not found by email',
        level=SentryLogLevel.WARNING,
        data={
            'email': email,
            'logout_token': 'test_token',
        },
    )


def test_process_logout_by_email__inactive_user__log_sentry(mocker):
    # arrange
    create_test_admin(
        email='inactive@example.com',
        status=UserStatus.INACTIVE,
    )
    email = 'inactive@example.com'
    logout_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._logout_user',
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    service = OktaLogoutService(logout_token='test_token')

    # act
    service._process_logout_by_email(email)

    # assert
    logout_user_mock.assert_not_called()
    capture_sentry_mock.assert_called_once_with(
        message='Okta logout: user not found by email',
        level=SentryLogLevel.WARNING,
        data={
            'email': email,
            'logout_token': 'test_token',
        },
    )


def test_process_logout_email_format__user_found__ok(mocker):
    # arrange
    user = create_test_admin(email='test@example.com')
    email = 'test@example.com'
    logout_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._logout_user',
    )
    validate_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
        return_value=True,
    )
    service = OktaLogoutService(logout_token='test_token')

    sub_id_data = {
        'format': 'email',
        'email': email,
    }
    request_data = {
        'format': 'email',
        'sub_id_data': sub_id_data,
    }

    # act
    service.process_logout(**request_data)

    # assert
    validate_mock.assert_called_once()
    logout_user_mock.assert_called_once_with(user, okta_sub=None)


def test_process_logout_email_format__user_not_found__log_sentry(mocker):
    # arrange
    email = 'nonexistent@example.com'
    logout_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._logout_user',
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    validate_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
        return_value=True,
    )
    service = OktaLogoutService(logout_token='test_token')

    sub_id_data = {
        'format': 'email',
        'email': email,
    }
    request_data = {
        'format': 'email',
        'sub_id_data': sub_id_data,
    }

    # act
    service.process_logout(**request_data)

    # assert
    validate_mock.assert_called_once()
    logout_user_mock.assert_not_called()
    capture_sentry_mock.assert_called_once()


def test_process_logout_missing_sub_in_iss_sub_format__log_sentry(mocker):
    # arrange
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    validate_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
        return_value=True,
    )
    service = OktaLogoutService(logout_token='test_token')

    sub_id_data = {
        'format': 'iss_sub',
        'iss': 'https://dev-123456.okta.com/oauth2/default',
    }
    request_data = {
        'format': 'iss_sub',
        'sub_id_data': sub_id_data,
    }

    # act
    service.process_logout(**request_data)

    # assert
    validate_mock.assert_called_once()
    capture_sentry_mock.assert_called_once_with(
        message="Missing 'sub' field in iss_sub format",
        level=SentryLogLevel.ERROR,
        data={'request_data': request_data},
    )


def test_process_logout_missing_email_in_email_format__log_sentry(mocker):
    # arrange
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    validate_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
        return_value=True,
    )
    service = OktaLogoutService(logout_token='test_token')

    sub_id_data = {
        'format': 'email',
    }
    request_data = {
        'format': 'email',
        'sub_id_data': sub_id_data,
    }

    # act
    service.process_logout(**request_data)

    # assert
    validate_mock.assert_called_once()
    capture_sentry_mock.assert_called_once_with(
        message="Missing 'email' field in email format",
        level=SentryLogLevel.ERROR,
        data={'request_data': request_data},
    )


def test_process_logout__unsupported_format__log_sentry(mocker):
    # arrange
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    validate_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
        return_value=True,
    )
    service = OktaLogoutService(logout_token='test_token')

    request_data = {
        'format': 'unsupported_format',
        'sub_id_data': {},
    }

    # act
    service.process_logout(**request_data)

    # assert
    validate_mock.assert_called_once()
    capture_sentry_mock.assert_called_once_with(
        message='Unsupported format: unsupported_format',
        level=SentryLogLevel.ERROR,
        data={'request_data': request_data},
    )


def test_process_logout__invalid_token__return_early(mocker):
    # arrange
    validate_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
        return_value=False,
    )
    process_by_sub_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._process_logout_by_sub',
    )
    service = OktaLogoutService(logout_token='invalid_token')

    sub_id_data = {
        'format': 'iss_sub',
        'iss': 'https://dev-123456.okta.com/oauth2/default',
        'sub': '00uid4BxXw6I6TV4m0g3',
    }
    request_data = {
        'format': 'iss_sub',
        'sub_id_data': sub_id_data,
    }

    # act
    service.process_logout(**request_data)

    # assert
    validate_mock.assert_called_once()
    process_by_sub_mock.assert_not_called()
