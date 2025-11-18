from unittest.mock import Mock

import pytest
import requests
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed

from src.accounts.enums import SourceType
from src.authentication.models import AccessToken
from src.authentication.services import exceptions
from src.authentication.services.okta import OktaService
from src.processes.tests.fixtures import create_test_user
from src.utils.logging import SentryLogLevel

pytestmark = pytest.mark.django_db
UserModel = get_user_model()


def test_get_auth_uri__ok(mocker):
    # arrange
    domain = 'dev-123456.okta.com'
    client_id = 'test_client_id'
    redirect_uri = 'https://some.redirect/uri'
    state = 'YrtkHpALzeTDnliK'

    settings_mock = mocker.patch(
        'src.authentication.services.okta.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.OKTA_CLIENT_ID = client_id
    settings_mock.OKTA_REDIRECT_URI = redirect_uri
    settings_mock.PROJECT_CONF = {'SSO_AUTH': True}
    set_cache_mock = mocker.patch(
        'src.authentication.services.okta.OktaService._set_cache',
    )
    mocker.patch(
        'src.authentication.services.okta.uuid4',
        return_value=state,
    )
    mocker.patch(
        'src.authentication.services.okta.base64.urlsafe_b64encode',
        side_effect=lambda x: Mock(decode=Mock(return_value='mocked_value')),
    )
    mocker.patch(
        'src.authentication.services.okta.secrets.token_bytes',
        return_value=b'test_bytes',
    )
    mocker.patch(
        'src.authentication.services.okta.hashlib.sha256',
        return_value=Mock(digest=Mock(return_value=b'test_digest')),
    )

    service = OktaService()

    # act
    result = service.get_auth_uri()

    # assert
    set_cache_mock.assert_called_once_with(value='mocked_value', key=state)
    expected_base = f'https://{domain}/oauth2/default/v1/authorize'
    assert result.startswith(expected_base)
    assert f'client_id={client_id}' in result
    assert f'state={state}' in result


def test_get_user_data__ok(mocker):
    # arrange
    user_profile = {
        'sub': '00uid4BxXw6I6TV4m0g3',
        'email': 'john.doe@example.com',
        'given_name': 'John',
        'family_name': 'Doe',
        'email_verified': True,
    }
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta.capture_sentry_message',
    )
    service = OktaService()

    # act
    result = service.get_user_data(user_profile)

    # assert
    assert result['email'] == 'john.doe@example.com'
    assert result['first_name'] == 'John'
    assert result['last_name'] == 'Doe'

    capture_sentry_mock.assert_called_once_with(
        message='Okta user profile john.doe@example.com',
        data={
            'first_name': 'John',
            'last_name': 'Doe',
            'user_profile': user_profile,
            'email': 'john.doe@example.com',
        },
        level=SentryLogLevel.INFO,
    )


def test_get_user_data__no_first_name__set_default(mocker):
    # arrange
    user_profile = {
        'sub': '00uid4BxXw6I6TV4m0g3',
        'email': 'test@example.com',
    }
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta.capture_sentry_message',
    )
    service = OktaService()

    # act
    result = service.get_user_data(user_profile)

    # assert
    assert result['email'] == 'test@example.com'
    assert result['first_name'] == 'test'
    assert result['last_name'] == ''
    capture_sentry_mock.assert_called_once_with(
        message='Okta user profile test@example.com',
        data={
            'first_name': 'test',
            'last_name': '',
            'user_profile': user_profile,
            'email': 'test@example.com',
        },
        level=SentryLogLevel.INFO,
    )


def test_get_user_data__email_not_found__raise_exception(mocker):
    # arrange
    user_profile = {
        'sub': '00uid4BxXw6I6TV4m0g3',
        'email': '',
    }
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta.capture_sentry_message',
    )
    service = OktaService()

    # act
    with pytest.raises(exceptions.EmailNotExist):
        service.get_user_data(user_profile)

    # assert
    capture_sentry_mock.assert_not_called()


def test_get_first_access_token__ok(mocker):
    # arrange
    state = 'test_state'
    code = 'test_code'
    code_verifier = 'test_code_verifier'
    domain = 'dev-123456.okta.com'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    redirect_uri = 'https://some.redirect/uri'
    response_data = {
        'access_token': 'test_access_token',
        'token_type': 'Bearer',
        'expires_in': 3600,
    }
    response_mock = Mock()
    response_mock.status_code = 200
    response_mock.json.return_value = response_data
    request_mock = mocker.patch(
        'src.authentication.services.okta.requests.post',
        return_value=response_mock,
    )
    get_cache_mock = mocker.patch(
        'src.authentication.services.okta.OktaService._get_cache',
        return_value=code_verifier,
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.OKTA_CLIENT_ID = client_id
    settings_mock.OKTA_CLIENT_SECRET = client_secret
    settings_mock.OKTA_REDIRECT_URI = redirect_uri
    settings_mock.PROJECT_CONF = {'SSO_AUTH': True}
    service = OktaService()

    # act
    result = service._get_first_access_token(code, state)

    # assert
    assert result == 'test_access_token'
    assert service.tokens == response_data
    get_cache_mock.assert_called_once_with(key=state)
    request_mock.assert_called_once_with(
        f'https://{domain}/oauth2/default/v1/token',
        data={
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'code': 'test_code',
            'redirect_uri': redirect_uri,
            'code_verifier': code_verifier,
        },
        timeout=10,
    )


def test_get_first_access_token__clear_cache__raise_exception(mocker):
    # arrange
    state = 'test_state'
    code = 'test_code'
    get_cache_mock = mocker.patch(
        'src.authentication.services.okta.OktaService._get_cache',
        return_value=None,
    )
    request_mock = mocker.patch(
        'src.authentication.services.okta.requests.post',
    )
    service = OktaService()

    # act
    with pytest.raises(exceptions.TokenInvalidOrExpired):
        service._get_first_access_token(code, state)

    # assert
    get_cache_mock.assert_called_once_with(key=state)
    request_mock.assert_not_called()


def test_get_first_access_token__request_error__raise_exception(mocker):
    # arrange
    state = 'test_state'
    code = 'test_code'
    code_verifier = 'test_code_verifier'
    domain = 'dev-123456.okta.com'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    redirect_uri = 'https://some.redirect/uri'

    get_cache_mock = mocker.patch(
        'src.authentication.services.okta.OktaService._get_cache',
        return_value=code_verifier,
    )
    request_mock = mocker.patch(
        'src.authentication.services.okta.requests.post',
        side_effect=requests.RequestException('HTTP Error'),
    )
    sentry_mock = mocker.patch(
        'src.authentication.services.okta.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.OKTA_CLIENT_ID = client_id
    settings_mock.OKTA_CLIENT_SECRET = client_secret
    settings_mock.OKTA_REDIRECT_URI = redirect_uri
    settings_mock.PROJECT_CONF = {'SSO_AUTH': True}
    service = OktaService()

    # act
    with pytest.raises(exceptions.TokenInvalidOrExpired):
        service._get_first_access_token(code, state)

    # assert
    get_cache_mock.assert_called_once_with(key=state)
    request_mock.assert_called_once()
    sentry_mock.assert_called_once_with(
        message='Get Okta access token return an error: HTTP Error',
        level=SentryLogLevel.ERROR,
    )


def test_get_user_profile__ok(mocker):
    # arrange
    access_token = 'test_access_token'
    domain = 'dev-123456.okta.com'
    response_data = {
        'sub': '00uid4BxXw6I6TV4m0g3',
        'email': 'test@example.com',
        'given_name': 'Test',
        'family_name': 'User',
    }
    response_mock = Mock()
    response_mock.status_code = 200
    response_mock.json.return_value = response_data
    request_mock = mocker.patch(
        'src.authentication.services.okta.requests.get',
        return_value=response_mock,
    )
    get_cache_mock = mocker.patch(
        'src.authentication.services.okta.OktaService._get_cache',
        return_value=None,
    )
    set_cache_mock = mocker.patch(
        'src.authentication.services.okta.OktaService._set_cache',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.PROJECT_CONF = {'SSO_AUTH': True}
    service = OktaService()

    # act
    result = service._get_user_profile(access_token)

    # assert
    assert result == response_data
    get_cache_mock.assert_called_once_with(key=f'user_profile_{access_token}')
    set_cache_mock.assert_called_once_with(
        value=response_data, key=f'user_profile_{access_token}',
    )
    request_mock.assert_called_once_with(
        f'https://{domain}/oauth2/default/v1/userinfo',
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=10,
    )


def test_get_user_profile__request_error__raise_exception(mocker):
    # arrange
    access_token = 'test_access_token'
    domain = 'dev-123456.okta.com'
    get_cache_mock = mocker.patch(
        'src.authentication.services.okta.OktaService._get_cache',
        return_value=None,
    )
    request_mock = mocker.patch(
        'src.authentication.services.okta.requests.get',
        side_effect=requests.RequestException('HTTP Error'),
    )
    sentry_mock = mocker.patch(
        'src.authentication.services.okta.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.PROJECT_CONF = {'SSO_AUTH': True}
    service = OktaService()

    # act
    with pytest.raises(exceptions.TokenInvalidOrExpired):
        service._get_user_profile(access_token)

    # assert
    get_cache_mock.assert_called_once_with(key=f'user_profile_{access_token}')
    request_mock.assert_called_once()
    sentry_mock.assert_called_once_with(
        message='Okta user profile request failed: HTTP Error',
        level=SentryLogLevel.ERROR,
    )


def test_save_tokens_for_user__create__ok():
    # arrange
    user = create_test_user()
    access_token = 'test_access_token'
    expires_in = 3600
    tokens_data = {
        'access_token': access_token,
        'expires_in': expires_in,
    }
    service = OktaService()
    service.tokens = tokens_data

    # act
    service.save_tokens_for_user(user)

    # assert
    token = AccessToken.objects.get(
        user=user,
        source=SourceType.OKTA,
    )
    assert token.access_token == access_token
    assert token.refresh_token == ''
    assert token.expires_in == expires_in


def test_save_tokens_for_user__update__ok():
    # arrange
    user = create_test_user()
    old_token = AccessToken.objects.create(
        source=SourceType.OKTA,
        user=user,
        refresh_token='',
        access_token='old_access_token',
        expires_in=1800,
    )
    new_tokens_data = {
        'access_token': 'new_access_token',
        'expires_in': 3600,
    }
    service = OktaService()
    service.tokens = new_tokens_data

    # act
    service.save_tokens_for_user(user)

    # assert
    old_token.refresh_from_db()
    assert old_token.access_token == new_tokens_data['access_token']
    assert old_token.refresh_token == ''
    assert old_token.expires_in == new_tokens_data['expires_in']


def test_authenticate_user__existing_user__ok(mocker):
    # arrange
    user = create_test_user(email='test@example.com')
    token = 'test_token'
    access_token = 'okta_access_token'
    code = 'test_code'
    state = 'test_state'
    user_agent = 'Test-Agent'
    user_ip = '127.0.0.1'
    user_profile = {
        'sub': '00uid4BxXw6I6TV4m0g3',
        'email': 'test@example.com',
        'given_name': 'Test',
        'family_name': 'User',
    }
    user_data_dict = {
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
    }

    get_first_access_token_mock = mocker.patch(
        'src.authentication.services.okta.'
        'OktaService._get_first_access_token',
        return_value=access_token,
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.okta.OktaService._get_user_profile',
        return_value=user_profile,
    )
    get_user_data_mock = mocker.patch(
        'src.authentication.services.okta.OktaService.get_user_data',
        return_value=user_data_dict,
    )

    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService.get_auth_token',
        return_value=token,
    )
    user_get_mock = mocker.patch(
        'src.authentication.services.okta.UserModel.objects.active',
    )
    user_get_mock.return_value.get.return_value = user
    save_tokens_mock = mocker.patch(
        'src.authentication.services.okta.OktaService.save_tokens_for_user',
    )
    analytics_mock = mocker.patch(
        'src.authentication.services.okta.AnalyticService.users_logged_in',
    )

    service = OktaService()

    # act
    result_user, result_token = service.authenticate_user(
        code,
        state,
        user_agent,
        user_ip,
    )

    # assert
    assert result_user == user
    assert result_token == token
    get_first_access_token_mock.assert_called_once_with(code, state)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_data_mock.assert_called_once_with(user_profile)
    user_get_mock.return_value.get.assert_called_once_with(
        email='test@example.com',
    )
    get_auth_token_mock.assert_called_once_with(
        user=user,
        user_agent=user_agent,
        user_ip=user_ip,
    )
    save_tokens_mock.assert_called_once_with(user)
    analytics_mock.assert_called_once()


def test_authenticate_user__new_user_signup_disabled__raise_exception(mocker):
    # arrange
    code = 'test_code'
    state = 'test_state'
    access_token = 'test_access_token'
    user_profile = {
        'sub': '00uid4BxXw6I6TV4m0g3',
        'email': 'newuser@example.com',
        'given_name': 'New',
        'family_name': 'User',
    }
    user_data_dict = {
        'email': 'newuser@example.com',
        'first_name': 'New',
        'last_name': 'User',
    }

    get_first_access_token_mock = mocker.patch(
        'src.authentication.services.okta.'
        'OktaService._get_first_access_token',
        return_value=access_token,
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.okta.OktaService._get_user_profile',
        return_value=user_profile,
    )
    get_user_data_mock = mocker.patch(
        'src.authentication.services.okta.OktaService.get_user_data',
        return_value=user_data_dict,
    )

    user_get_mock = mocker.patch(
        'src.authentication.services.okta.UserModel.objects.active',
    )
    user_get_mock.return_value.get.side_effect = UserModel.DoesNotExist()
    settings_mock = mocker.patch(
        'src.authentication.services.okta.settings',
    )
    settings_mock.PROJECT_CONF = {'SIGNUP': False}
    settings_mock.PROJECT_CONF = {'SSO_AUTH': True}
    service = OktaService()

    # act
    with pytest.raises(AuthenticationFailed):
        service.authenticate_user(code, state)

    # assert
    get_first_access_token_mock.assert_called_once_with(code, state)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_data_mock.assert_called_once_with(user_profile)
    user_get_mock.return_value.get.assert_called_once_with(
        email='newuser@example.com',
    )
