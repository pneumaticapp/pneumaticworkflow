from unittest.mock import Mock

import pytest
import requests
from django.contrib.auth import get_user_model

from src.accounts.enums import (
    SourceType,
)
from src.authentication.entities import SSOConfigData
from src.authentication.messages import MSG_AU_0018
from src.authentication.models import AccessToken
from src.authentication.services import exceptions
from src.authentication.services.auth0 import (
    Auth0Service,
)
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_account,
)
from src.utils.logging import SentryLogLevel

pytestmark = pytest.mark.django_db
UserModel = get_user_model()


def test__get_auth_uri__ok(mocker):

    # arrange
    domain = 'test_client_domain'
    client_id = 'test_client_id'
    redirect_uri = 'test_redirect_uri'
    state_uuid = 'YrtkHpALzeTDnliK'
    encrypted_domain = 'encrypted_domain_test'
    state = f"{state_uuid}{encrypted_domain}"
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.auth0.settings',
        new=settings_mock,
    )
    settings_mock.AUTH0_DOMAIN = domain
    settings_mock.AUTH0_CLIENT_ID = client_id
    settings_mock.AUTH0_CLIENT_SECRET = 'test_secret'
    settings_mock.AUTH0_REDIRECT_URI = redirect_uri
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'auth0',
    }
    set_cache_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._set_cache',
    )
    mocker.patch(
        'src.authentication.services.auth0.uuid4',
        return_value=state_uuid,
    )
    encrypt_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.encrypt',
        return_value=encrypted_domain,
    )
    service = Auth0Service()

    # act
    result = service.get_auth_uri()

    # assert
    query_params = (
        f'client_id={client_id}&redirect_uri={redirect_uri}&'
        f'scope=openid+email+profile+offline_access&state={state}&'
        f'response_type=code'
    )
    set_cache_mock.assert_called_once_with(value=True, key=state)
    assert result == f'https://{domain}/authorize?{query_params}'
    encrypt_mock.assert_called_once_with(domain)


def test_get_user_data__ok(mocker):

    # arrange
    user_profile = {
        'sub': 'auth0|123456',
        'email': 'test@example.com',
        'given_name': 'Test',
        'family_name': 'User',
        'job_title': 'Test',
        'picture': 'https://example.com/photo.jpg',
    }
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.auth0.settings',
        new=settings_mock,
    )
    settings_mock.AUTH0_CLIENT_SECRET = 'test_secret'
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'auth0',
    }
    service = Auth0Service()

    # act
    result = service.get_user_data(user_profile)

    # assert
    assert result['email'] == user_profile['email']
    assert result['first_name'] == user_profile['given_name']
    assert result['last_name'] == user_profile['family_name']
    assert result['job_title'] == user_profile['job_title']
    assert result['photo'] == user_profile['picture']

    capture_sentry_mock.assert_called_once_with(
        message=f'Auth0 user profile {user_profile["email"]}',
        data={
            'photo': user_profile['picture'],
            'first_name': user_profile['given_name'],
            'user_profile': user_profile,
            'email': user_profile['email'],
        },
        level=SentryLogLevel.INFO,
    )


def test_get_user_data__not_first_name__set_default(mocker):
    # arrange
    user_profile = {
        'sub': 'auth0|123456',
        'email': 'test@example.com',
        'job_title': 'Test',
        'picture': 'https://example.com/photo.jpg',
    }
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.auth0.settings',
        new=settings_mock,
    )
    settings_mock.AUTH0_CLIENT_SECRET = 'test_secret'
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'auth0',
    }
    service = Auth0Service()

    # act
    result = service.get_user_data(user_profile)

    # assert
    assert result['email'] == user_profile['email']
    assert result['first_name'] == 'test'
    assert result['last_name'] == ''
    assert result['job_title'] == user_profile['job_title']
    assert result['photo'] == user_profile['picture']
    capture_sentry_mock.assert_called_once_with(
        message=f'Auth0 user profile {user_profile["email"]}',
        data={
            'photo': user_profile['picture'],
            'first_name': 'test',
            'user_profile': user_profile,
            'email': user_profile['email'],
        },
        level=SentryLogLevel.INFO,
    )


def test_get_user_data__email_not_found__raise_exception(mocker):
    # arrange
    user_profile = {
        'sub': 'auth0|123456',
        'email': '',
        'job_title': 'Test',
        'picture': 'https://example.com/photo.jpg',
    }
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.auth0.settings',
        new=settings_mock,
    )
    settings_mock.AUTH0_CLIENT_SECRET = 'test_secret'
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'auth0',
    }
    service = Auth0Service()

    # act
    with pytest.raises(exceptions.EmailNotExist):
        service.get_user_data(user_profile)

    # assert
    capture_sentry_mock.assert_not_called()


def test_get_first_access_token__ok(mocker):

    # arrange
    state = 'ASDSDasd12'
    code = 'test_code'
    domain = 'test_client_domain'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    redirect_uri = 'test_redirect_uri'
    response_data = {
        'access_token': 'test_access_token',
        'refresh_token': 'test_refresh_token',
        'token_type': 'Bearer',
        'expires_in': 3600,
    }
    response_mock = Mock(ok=True)
    response_mock.status_code = 200
    response_mock.json.return_value = response_data
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.post',
        return_value=response_mock,
    )
    get_cache_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_cache',
        return_value=True,
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.auth0.settings',
        new=settings_mock,
    )
    sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message',
    )
    settings_mock.AUTH0_DOMAIN = domain
    settings_mock.AUTH0_CLIENT_ID = client_id
    settings_mock.AUTH0_CLIENT_SECRET = client_secret
    settings_mock.AUTH0_REDIRECT_URI = redirect_uri
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'auth0',
    }
    service = Auth0Service()

    # act
    result = service._get_first_access_token(code, state)

    # assert
    assert result == 'test_access_token'
    assert service.tokens == response_data
    get_cache_mock.assert_called_once_with(key=state)
    request_mock.assert_called_once_with(
        f'https://{domain}/oauth/token',
        data={
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'code': 'test_code',
            'redirect_uri': redirect_uri,
        },
        timeout=10,
    )
    sentry_mock.assert_not_called()


def test_get_first_access_token__clear_cache__raise_exception(mocker):

    # arrange
    state = 'ASDSDasd12'
    code = 'test_code'
    get_cache_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_cache',
        return_value=None,
    )
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.post',
    )
    sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.auth0.settings',
        new=settings_mock,
    )
    settings_mock.AUTH0_CLIENT_SECRET = 'test_secret'
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'auth0',
    }
    service = Auth0Service()

    # act
    with pytest.raises(exceptions.TokenInvalidOrExpired):
        service._get_first_access_token(code, state)

    # assert
    get_cache_mock.assert_called_once_with(key=state)
    request_mock.assert_not_called()
    sentry_mock.assert_not_called()


def test_get_first_access_token__request_return_error__raise_exception(mocker):

    # arrange
    state = 'ASDSDasd12'
    code = 'test_code'
    domain = 'test_client_domain'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    redirect_uri = 'test_redirect_uri'

    get_cache_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_cache',
        return_value=True,
    )
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.post',
        side_effect=requests.RequestException('HTTP Error'),
    )
    sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.auth0.settings',
        new=settings_mock,
    )
    settings_mock.AUTH0_DOMAIN = domain
    settings_mock.AUTH0_CLIENT_ID = client_id
    settings_mock.AUTH0_CLIENT_SECRET = client_secret
    settings_mock.AUTH0_REDIRECT_URI = redirect_uri
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'auth0',
    }
    service = Auth0Service()

    # act
    with pytest.raises(exceptions.TokenInvalidOrExpired):
        service._get_first_access_token(code, state)

    # assert
    get_cache_mock.assert_called_once_with(key=state)
    request_mock.assert_called_once_with(
        f'https://{domain}/oauth/token',
        data={
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'code': 'test_code',
            'redirect_uri': redirect_uri,
        },
        timeout=10,
    )
    sentry_mock.assert_called_once_with(
        message='Get Auth0 access token return an error: HTTP Error',
        level=SentryLogLevel.ERROR,
    )


def test_get_user_profile__ok(mocker):

    # arrange
    access_token = 'Q@#!@adad123'
    domain = 'test_client_domain'
    response_data = {
        'sub': 'auth0|123456',
        'email': 'test@example.com',
        'given_name': 'Test',
        'family_name': 'User',
    }
    response_mock = Mock(ok=True)
    response_mock.status_code = 200
    response_mock.json.return_value = response_data
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.get',
        return_value=response_mock,
    )
    get_cache_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_cache',
        return_value=None,
    )
    set_cache_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._set_cache',
    )
    sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.auth0.settings',
        new=settings_mock,
    )
    settings_mock.AUTH0_DOMAIN = domain
    settings_mock.AUTH0_CLIENT_SECRET = 'test_secret'
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'auth0',
    }
    service = Auth0Service()

    # act
    result = service._get_user_profile(access_token)

    # assert
    assert result == response_data
    get_cache_mock.assert_called_once_with(key=f'user_profile_{access_token}')
    set_cache_mock.assert_called_once_with(
        value=response_data, key=f'user_profile_{access_token}',
    )
    request_mock.assert_called_once_with(
        f'https://{domain}/userinfo',
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=10,
    )
    sentry_mock.assert_not_called()


def test_get_user_profile__response_error__raise_exception(mocker):

    # arrange
    access_token = 'Q@#!@adad123'
    domain = 'test_client_domain'
    get_cache_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_cache',
        return_value=None,
    )
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.get',
        side_effect=requests.RequestException('HTTP Error'),
    )
    sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message',
    )
    mocker.patch(
        'src.authentication.services.auth0.Auth0Service._set_cache',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.auth0.settings',
        new=settings_mock,
    )
    settings_mock.AUTH0_DOMAIN = domain
    settings_mock.AUTH0_CLIENT_SECRET = 'test_secret'
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'auth0',
    }
    service = Auth0Service()

    # act
    with pytest.raises(exceptions.TokenInvalidOrExpired) as ex:
        service._get_user_profile(access_token)

    # assert
    assert str(ex.value) == "Token is expired."
    get_cache_mock.assert_called_once_with(key=f'user_profile_{access_token}')
    request_mock.assert_called_once_with(
        f'https://{domain}/userinfo',
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=10,
    )
    sentry_mock.assert_called_once_with(
        message='Auth0 user profile request failed: HTTP Error',
        level=SentryLogLevel.ERROR,
    )


def test_save_tokens_for_user__create__ok(mocker):

    # arrange
    user = create_test_admin()
    refresh_token = 'some refresh'
    access_token = 'some access'
    token_type = 'Bearer'
    expires_in = 300
    tokens_data = {
        'refresh_token': refresh_token,
        'access_token': access_token,
        'token_type': token_type,
        'expires_in': expires_in,
    }
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.auth0.settings',
        new=settings_mock,
    )
    settings_mock.AUTH0_CLIENT_SECRET = 'test_secret'
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'auth0',
    }
    service = Auth0Service()
    service.tokens = tokens_data

    # act
    service.save_tokens_for_user(user)

    # assert
    token = AccessToken.objects.get(
        user=user,
        source=SourceType.AUTH0,
    )
    assert token.access_token == access_token
    assert token.refresh_token == refresh_token
    assert token.expires_in == expires_in


def test_save_tokens_for_user__update__ok(mocker):
    # arrange
    user = create_test_admin()
    token_type = 'Bearer'
    token = AccessToken.objects.create(
        source=SourceType.AUTH0,
        user=user,
        refresh_token='ahsdsdasd23ggfn',
        access_token=f'{token_type} !@#asas',
        expires_in=360,
    )
    new_tokens_data = {
        'refresh_token': 'new refresh',
        'access_token': 'new access token',
        'token_type': token_type,
        'expires_in': 400,
    }
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.auth0.settings',
        new=settings_mock,
    )
    settings_mock.AUTH0_CLIENT_SECRET = 'test_secret'
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'auth0',
    }
    service = Auth0Service()
    service.tokens = new_tokens_data

    # act
    service.save_tokens_for_user(user)

    # assert
    token.refresh_from_db()
    assert token.access_token == new_tokens_data['access_token']
    assert token.refresh_token == new_tokens_data['refresh_token']
    assert token.expires_in == new_tokens_data['expires_in']


def test_authenticate_user__existing_user__ok(mocker):
    # arrange
    user = create_test_admin(email='test@example.com')
    token = 'test_token'
    access_token = 'auth0_access_token'
    code = 'test_code'
    state = 'test_state'
    user_agent = 'Test-Agent'
    user_ip = '127.0.0.1'
    user_profile = {
        'sub': 'auth0|123456',
        'email': 'test@example.com',
        'given_name': 'Test',
        'family_name': 'User',
    }
    user_data = {
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
    }
    get_first_access_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_first_access_token',
        return_value=access_token,
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_user_profile',
        return_value=user_profile,
    )
    get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.get_user_data',
        return_value=user_data,
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService.get_auth_token',
        return_value=token,
    )
    user_get_mock = mocker.patch(
        'src.authentication.services.auth0.UserModel.objects.active',
    )
    user_get_mock.return_value.get.return_value = user
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.save_tokens_for_user',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.auth0.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'auth0',
    }
    settings_mock.AUTH0_CLIENT_SECRET = 'test_secret'

    service = Auth0Service()

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
        user_agent='Test-Agent',
        user_ip='127.0.0.1',
    )
    save_tokens_mock.assert_called_once_with(user)


def test_get_config__domain_not_found_fallback_to_default__ok(mocker):
    """If domain configuration is not found, default configuration is used."""
    # arrange
    domain = 'nonexistent.domain.com'
    default_client_id = 'default_client_id'
    default_client_secret = 'default_client_secret'
    default_domain = 'dev-default.auth0.com'
    default_redirect_uri = 'https://default.redirect/uri'
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.auth0.settings',
        new=settings_mock,
    )
    settings_mock.AUTH0_CLIENT_ID = default_client_id
    settings_mock.AUTH0_CLIENT_SECRET = default_client_secret
    settings_mock.AUTH0_DOMAIN = default_domain
    settings_mock.AUTH0_REDIRECT_URI = default_redirect_uri
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'auth0',
    }

    # act
    service = Auth0Service(domain=domain)

    # assert
    assert service.config.client_id == default_client_id
    assert service.config.client_secret == default_client_secret
    assert service.config.domain == default_domain
    assert service.config.redirect_uri == default_redirect_uri


def test_get_config__domain_not_found_and_no_default__raise_exception(mocker):
    """
    If domain configuration is not found
    and default configuration is also unavailable, an exception is raised
    with a message about incorrect SSO configuration.
    """
    # arrange
    domain = 'nonexistent.domain.com'
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.auth0.settings',
        new=settings_mock,
    )
    settings_mock.AUTH0_CLIENT_SECRET = None
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'auth0',
    }

    # act
    with pytest.raises(exceptions.Auth0ServiceException) as exc_info:
        Auth0Service(domain=domain)

    # assert
    assert str(exc_info.value) == MSG_AU_0018(domain)


def test_authenticate_user__join_existing_account__ok(mocker):
    # arrange
    existing_account = create_test_account()
    user = create_test_admin(
        account=existing_account,
        email='newuser@example.com',
    )
    token = 'test_token'
    access_token = 'test_access_token'
    code = 'test_code'
    state = 'test_state'
    user_agent = 'Test-Agent'
    user_ip = '127.0.0.1'
    user_profile = {
        'sub': 'auth0|123456',
        'email': 'newuser@example.com',
        'given_name': 'New',
        'family_name': 'User',
    }
    user_data = {
        'email': 'newuser@example.com',
        'first_name': 'New',
        'last_name': 'User',
    }
    get_first_access_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_first_access_token',
        return_value=access_token,
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_user_profile',
        return_value=user_profile,
    )
    get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.get_user_data',
        return_value=user_data,
    )
    user_get_mock = mocker.patch(
        'src.authentication.services.auth0.UserModel.objects.active',
    )
    user_get_mock.return_value.get.side_effect = UserModel.DoesNotExist()
    sso_config_mock = mocker.patch(
        'src.authentication.services.auth0.SSOConfig.objects.get',
    )
    sso_config_obj = Mock()
    sso_config_obj.account = existing_account
    sso_config_mock.return_value = sso_config_obj
    join_existing_account_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.join_existing_account',
        return_value=(user, token),
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.save_tokens_for_user',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.auth0.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SIGNUP': True,
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'auth0',
    }
    get_config_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_config',
    )
    get_config_mock.return_value = SSOConfigData(
        client_id='test_client_id',
        client_secret='test_client_secret',
        domain='example.com',
        redirect_uri='http://localhost/oauth/auth0',
    )
    service = Auth0Service()
    service.tokens = {'access_token': 'test_token'}

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
        email='newuser@example.com',
    )
    join_existing_account_mock.assert_called_once_with(
        account=existing_account,
        user_agent=user_agent,
        user_ip=user_ip,
        **user_data,
    )
    save_tokens_mock.assert_called_once_with(user)
