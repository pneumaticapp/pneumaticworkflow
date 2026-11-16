from unittest.mock import Mock

import pytest
import requests
from django.contrib.auth import get_user_model

from src.accounts.enums import (
    SourceType,
)
from src.accounts.enums import UserStatus, UserInviteStatus
from src.accounts.models import UserInvite
from src.accounts.serializers.user import UserWebsocketSerializer
from src.authentication.enums import AuthTokenType
from src.authentication.messages import (
    MSG_AU_0018,
    MSG_AU_0021,
)
from src.authentication.models import (
    AccessToken,
)
from src.authentication.services import exceptions
from src.authentication.services.auth0 import (
    Auth0Service,
)
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_admin,
    create_test_account,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
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
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.save_tokens_for_user',
    )
    users_logged_in_mock = mocker.patch(
        'src.analysis.services.AnalyticService.users_logged_in',
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
    get_auth_token_mock.assert_called_once_with(
        user=user,
        user_agent=user_agent,
        user_ip=user_ip,
    )
    save_tokens_mock.assert_called_once_with(user)
    users_logged_in_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        source=SourceType.AUTH0,
    )


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


def test_authenticate_user__invited_user_activated__ok(mocker):
    """Test that invited user is activated using UserInviteService."""
    # arrange
    account = create_test_account()
    invited_user = create_test_admin(
        email='invited@example.com',
        account=account,
        status=UserStatus.INVITED,
    )
    invited_user.is_active = False
    invited_user.save()
    UserInvite.objects.create(
        invited_user=invited_user,
        account=account,
        email=invited_user.email,
    )
    token = 'test_token'
    access_token = 'auth0_access_token'
    code = 'test_code'
    state = 'test_state'
    user_agent = 'Test-Agent'
    user_ip = '127.0.0.1'
    user_profile = {
        'sub': 'auth0|123456',
        'email': 'invited@example.com',
        'given_name': 'Updated',
        'family_name': 'Name',
        'picture': 'https://example.com/photo.jpg',
    }
    user_data = {
        'email': 'invited@example.com',
        'first_name': 'Updated',
        'last_name': 'Name',
        'photo': 'https://example.com/photo.jpg',
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
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.save_tokens_for_user',
    )
    mocker.patch(
        'src.processes.services.system_workflows.SystemWorkflowService'
        '.create_onboarding_workflows',
    )
    mocker.patch(
        'src.processes.services.system_workflows.SystemWorkflowService'
        '.create_activated_workflows',
    )
    mocker.patch(
        'src.accounts.services.account.AccountService.update_users_counts',
    )
    mocker.patch(
        'src.notifications.tasks.send_user_updated_notification.delay',
    )
    mocker.patch(
        'src.payment.tasks.increase_plan_users.delay',
    )
    mocker.patch(
        'src.analysis.services.AnalyticService.users_joined',
    )
    mocker.patch(
        'src.accounts.services.user_invite.UserInviteService.identify',
    )
    mocker.patch(
        'src.accounts.services.user_invite.UserInviteService.group',
    )
    users_logged_in_mock = mocker.patch(
        'src.analysis.services.AnalyticService.users_logged_in',
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
    invited_user.refresh_from_db()
    assert invited_user.status == UserStatus.ACTIVE
    assert invited_user.is_active is True
    assert invited_user.first_name == 'Updated'
    assert invited_user.last_name == 'Name'
    assert invited_user.photo == 'https://example.com/photo.jpg'
    invite = UserInvite.objects.get(invited_user=invited_user)
    assert invite.status == UserInviteStatus.ACCEPTED
    assert result_user == invited_user
    assert result_token == token
    get_first_access_token_mock.assert_called_once_with(code, state)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_data_mock.assert_called_once_with(user_profile)
    get_auth_token_mock.assert_called_once_with(
        user=invited_user,
        user_agent=user_agent,
        user_ip=user_ip,
    )
    save_tokens_mock.assert_called_once_with(invited_user)
    users_logged_in_mock.assert_called_once()


def test_authenticate_user__inactive_user__raise_exception(mocker):
    # arrange
    email = 'inactive@example.com'
    inactive_user = create_test_admin(
        email=email,
        status=UserStatus.INACTIVE,
    )
    access_token = 'auth0_access_token'
    code = 'test_code'
    state = 'test_state'
    user_agent = 'Test-Agent'
    user_ip = '127.0.0.1'
    user_profile = {
        'email': email,
    }
    user_data = {
        'email': email,
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
    join_existing_account_mock = mocker.patch(
        'src.authentication.services.base_sso.BaseSSOService'
        '.join_existing_account',
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService.get_auth_token',
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.save_tokens_for_user',
    )
    users_logged_in_mock = mocker.patch(
        'src.analysis.services.AnalyticService.users_logged_in',
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
    with pytest.raises(exceptions.Auth0ServiceException) as ex:
        service.authenticate_user(
            code=code,
            state=state,
            user_agent=user_agent,
            user_ip=user_ip,
        )

    # assert
    assert ex.value.message == MSG_AU_0021
    inactive_user.refresh_from_db()
    assert inactive_user.status == UserStatus.INACTIVE
    get_first_access_token_mock.assert_called_once_with(code, state)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_data_mock.assert_called_once_with(user_profile)
    join_existing_account_mock.assert_not_called()
    get_auth_token_mock.assert_not_called()
    save_tokens_mock.assert_not_called()
    users_logged_in_mock.assert_not_called()


def test_authenticate_user__inactive_and_active_users__login_active(mocker):
    # arrange
    email = 'user@example.com'
    create_test_admin(
        email=email,
        status=UserStatus.INACTIVE,
    )
    user = create_test_admin(email=email)
    token = 'test_token'
    access_token = 'auth0_access_token'
    code = 'test_code'
    state = 'test_state'
    user_agent = 'Test-Agent'
    user_ip = '127.0.0.1'
    user_profile = {
        'email': email,
    }
    user_data = {
        'email': email,
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
    join_existing_account_mock = mocker.patch(
        'src.authentication.services.base_sso.BaseSSOService'
        '.join_existing_account',
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService.get_auth_token',
        return_value=token,
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.save_tokens_for_user',
    )
    users_logged_in_mock = mocker.patch(
        'src.analysis.services.AnalyticService.users_logged_in',
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
        code=code,
        state=state,
        user_agent=user_agent,
        user_ip=user_ip,
    )

    # assert
    assert result_user == user
    assert result_token == token
    get_first_access_token_mock.assert_called_once_with(code, state)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_data_mock.assert_called_once_with(user_profile)
    join_existing_account_mock.assert_not_called()
    get_auth_token_mock.assert_called_once_with(
        user=user,
        user_agent=user_agent,
        user_ip=user_ip,
    )
    save_tokens_mock.assert_called_once_with(user)
    users_logged_in_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        source=SourceType.AUTH0,
    )


def test_authenticate_user__inactive_and_invited_users__activate_invited(
    mocker,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    email = 'invited@example.com'
    create_test_admin(
        email=email,
        account=account,
        status=UserStatus.INACTIVE,
    )
    invited_user = create_invited_user(
        user=owner,
        email=email,
    )
    token = 'test_token'
    access_token = 'auth0_access_token'
    code = 'test_code'
    state = 'test_state'
    user_agent = 'Test-Agent'
    user_ip = '127.0.0.1'
    user_profile = {
        'email': email,
    }
    user_data = {
        'email': email,
        'first_name': 'Updated',
        'last_name': 'Name',
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
    join_existing_account_mock = mocker.patch(
        'src.authentication.services.base_sso.BaseSSOService'
        '.join_existing_account',
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService.get_auth_token',
        return_value=token,
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.save_tokens_for_user',
    )
    create_onboarding_workflows_mock = mocker.patch(
        'src.processes.services.system_workflows.SystemWorkflowService'
        '.create_onboarding_workflows',
    )
    create_activated_workflows_mock = mocker.patch(
        'src.processes.services.system_workflows.SystemWorkflowService'
        '.create_activated_workflows',
    )
    update_users_counts_mock = mocker.patch(
        'src.accounts.services.account.AccountService.update_users_counts',
    )
    send_user_updated_notification_mock = mocker.patch(
        'src.notifications.tasks.send_user_updated_notification.delay',
    )
    increase_plan_users_mock = mocker.patch(
        'src.payment.tasks.increase_plan_users.delay',
    )
    users_joined_mock = mocker.patch(
        'src.analysis.services.AnalyticService.users_joined',
    )
    identify_mock = mocker.patch(
        'src.accounts.services.user_invite.UserInviteService.identify',
    )
    group_mock = mocker.patch(
        'src.accounts.services.user_invite.UserInviteService.group',
    )
    users_logged_in_mock = mocker.patch(
        'src.analysis.services.AnalyticService.users_logged_in',
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
        code=code,
        state=state,
        user_agent=user_agent,
        user_ip=user_ip,
    )

    # assert
    assert result_user == invited_user
    assert result_token == token
    invited_user.refresh_from_db()
    assert invited_user.status == UserStatus.ACTIVE
    assert invited_user.first_name == 'Updated'
    assert invited_user.last_name == 'Name'
    invite = UserInvite.objects.get(invited_user=invited_user)
    assert invite.status == UserInviteStatus.ACCEPTED
    get_first_access_token_mock.assert_called_once_with(code, state)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_data_mock.assert_called_once_with(user_profile)
    join_existing_account_mock.assert_not_called()
    create_onboarding_workflows_mock.assert_called_once_with()
    create_activated_workflows_mock.assert_called_once_with()
    update_users_counts_mock.assert_called_once_with()
    send_user_updated_notification_mock.assert_called_once_with(
        logging=False,
        account_id=account.id,
        user_data=UserWebsocketSerializer(invited_user).data,
    )
    increase_plan_users_mock.assert_not_called()
    users_joined_mock.assert_called_once_with(invited_user)
    identify_mock.assert_called_once_with(invited_user)
    group_mock.assert_called_once_with(invited_user)
    get_auth_token_mock.assert_called_once_with(
        user=invited_user,
        user_agent=user_agent,
        user_ip=user_ip,
    )
    save_tokens_mock.assert_called_once_with(invited_user)
    users_logged_in_mock.assert_called_once_with(
        user=invited_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        source=SourceType.AUTH0,
    )


def test_authenticate_user__unknown_email__join_first_account(
    mocker,
    identify_mock,
):
    # arrange
    account_1 = create_test_account()
    create_test_owner(
        account=account_1,
        email='owner1@example.com',
    )
    account_2 = create_test_account()
    create_test_owner(
        account=account_2,
        email='owner2@example.com',
    )
    email = 'new@example.com'
    token = 'test_token'
    access_token = 'auth0_access_token'
    code = 'test_code'
    state = 'test_state'
    user_agent = 'Test-Agent'
    user_ip = '127.0.0.1'
    user_profile = {
        'email': email,
    }
    user_data = {
        'email': email,
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
    sync_account_file_fields_mock = mocker.patch(
        'src.accounts.services.user.sync_account_file_fields',
    )
    after_signup_mock = mocker.patch(
        'src.authentication.views.mixins.SignUpMixin.after_signup',
    )
    update_users_counts_mock = mocker.patch(
        'src.accounts.services.account.AccountService.update_users_counts',
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService.get_auth_token',
        return_value=token,
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.save_tokens_for_user',
    )
    users_logged_in_mock = mocker.patch(
        'src.analysis.services.AnalyticService.users_logged_in',
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
        code=code,
        state=state,
        user_agent=user_agent,
        user_ip=user_ip,
    )

    # assert
    assert result_token == token
    assert result_user.account_id == account_1.id
    assert result_user.email == email
    assert result_user.first_name == 'New'
    assert result_user.last_name == 'User'
    assert result_user.status == UserStatus.ACTIVE
    assert result_user.is_admin is True
    assert result_user.is_account_owner is False
    get_first_access_token_mock.assert_called_once_with(code, state)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_data_mock.assert_called_once_with(user_profile)
    identify_mock.assert_called_once_with(result_user)
    sync_account_file_fields_mock.assert_called_once_with(
        account=account_1,
        user=None,
        old_values=[None],
        new_values=[None],
    )
    after_signup_mock.assert_called_once_with(result_user)
    update_users_counts_mock.assert_called_once_with()
    get_auth_token_mock.assert_called_once_with(
        user=result_user,
        user_agent=user_agent,
        user_ip=user_ip,
    )
    save_tokens_mock.assert_called_once_with(result_user)
    users_logged_in_mock.assert_called_once_with(
        user=result_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        source=SourceType.AUTH0,
    )


def test_authenticate_user__guest_same_email__join_account(mocker):
    # arrange
    account = create_test_account()
    create_test_owner(
        account=account,
        email='owner@example.com',
    )
    email = 'guest@example.com'
    guest = create_test_guest(
        email=email,
        account=account,
    )
    new_user = create_test_not_admin(
        account=account,
        email='new@example.com',
    )
    token = 'test_token'
    access_token = 'auth0_access_token'
    code = 'test_code'
    state = 'test_state'
    user_agent = 'Test-Agent'
    user_ip = '127.0.0.1'
    user_profile = {
        'email': email,
    }
    user_data = {
        'email': email,
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
    join_existing_account_mock = mocker.patch(
        'src.authentication.services.base_sso.BaseSSOService'
        '.join_existing_account',
        return_value=new_user,
    )
    update_users_counts_mock = mocker.patch(
        'src.accounts.services.account.AccountService.update_users_counts',
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService.get_auth_token',
        return_value=token,
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.save_tokens_for_user',
    )
    users_logged_in_mock = mocker.patch(
        'src.analysis.services.AnalyticService.users_logged_in',
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
        code=code,
        state=state,
        user_agent=user_agent,
        user_ip=user_ip,
    )

    # assert
    assert result_user == new_user
    assert result_token == token
    guest.refresh_from_db()
    assert guest.status == UserStatus.ACTIVE
    get_first_access_token_mock.assert_called_once_with(code, state)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_data_mock.assert_called_once_with(user_profile)
    join_existing_account_mock.assert_called_once_with(
        account=account,
        **user_data,
    )
    update_users_counts_mock.assert_called_once_with()
    get_auth_token_mock.assert_called_once_with(
        user=new_user,
        user_agent=user_agent,
        user_ip=user_ip,
    )
    save_tokens_mock.assert_called_once_with(new_user)
    users_logged_in_mock.assert_called_once_with(
        user=new_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        source=SourceType.AUTH0,
    )


def test_authenticate_user__active_and_invited_users__login_active(mocker):
    # arrange
    account_1 = create_test_account()
    owner_1 = create_test_owner(
        account=account_1,
        email='owner1@example.com',
    )
    email = 'user@example.com'
    invited_user = create_invited_user(
        user=owner_1,
        email=email,
    )
    account_2 = create_test_account()
    user = create_test_admin(
        account=account_2,
        email=email,
    )
    token = 'test_token'
    access_token = 'auth0_access_token'
    code = 'test_code'
    state = 'test_state'
    user_agent = 'Test-Agent'
    user_ip = '127.0.0.1'
    user_profile = {
        'email': email,
    }
    user_data = {
        'email': email,
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
    accept_mock = mocker.patch(
        'src.accounts.services.user_invite.UserInviteService.accept',
    )
    join_existing_account_mock = mocker.patch(
        'src.authentication.services.base_sso.BaseSSOService'
        '.join_existing_account',
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService.get_auth_token',
        return_value=token,
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.save_tokens_for_user',
    )
    users_logged_in_mock = mocker.patch(
        'src.analysis.services.AnalyticService.users_logged_in',
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
        code=code,
        state=state,
        user_agent=user_agent,
        user_ip=user_ip,
    )

    # assert
    assert result_user == user
    assert result_token == token
    invited_user.refresh_from_db()
    assert invited_user.status == UserStatus.INVITED
    invite = UserInvite.objects.get(invited_user=invited_user)
    assert invite.status == UserInviteStatus.PENDING
    get_first_access_token_mock.assert_called_once_with(code, state)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_data_mock.assert_called_once_with(user_profile)
    accept_mock.assert_not_called()
    join_existing_account_mock.assert_not_called()
    get_auth_token_mock.assert_called_once_with(
        user=user,
        user_agent=user_agent,
        user_ip=user_ip,
    )
    save_tokens_mock.assert_called_once_with(user)
    users_logged_in_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        source=SourceType.AUTH0,
    )
