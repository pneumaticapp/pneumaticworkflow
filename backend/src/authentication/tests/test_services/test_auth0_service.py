import pytest
import requests
from unittest.mock import Mock
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from src.accounts.enums import (
    SourceType,
)
from src.accounts.models import Contact, Account
from src.authentication.messages import MSG_AU_0009
from src.authentication.models import AccessToken
from src.authentication.services import exceptions
from src.authentication.services.auth0 import (
    Auth0Service,
)
from src.processes.tests.fixtures import (
    create_test_user,
)
from src.utils.logging import SentryLogLevel

pytestmark = pytest.mark.django_db
UserModel = get_user_model()


def test__get_auth_uri__ok(mocker):

    # arrange
    domain = 'test_client_domain'
    client_id = 'test_client_id'
    redirect_uri = 'test_redirect_uri'
    state = 'YrtkHpALzeTDnliK'
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings',
    )
    settings_mock.AUTH0_DOMAIN = domain
    settings_mock.AUTH0_CLIENT_ID = client_id
    settings_mock.AUTH0_REDIRECT_URI = redirect_uri
    set_cache_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._set_cache'
    )
    mocker.patch(
        'src.authentication.services.auth0.uuid4',
        return_value=state
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
    set_cache_mock.assert_called_once_with(
        value=True, key=state
    )
    assert result == f'https://{domain}/authorize?{query_params}'


def test_get_user_data__ok(mocker):

    # arrange
    user_profile = {
        'sub': 'auth0|123456',
        'email': 'test@example.com',
        'given_name': 'Test',
        'family_name': 'User',
        'picture': 'https://example.com/photo.jpg'
    }
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message'
    )
    service = Auth0Service()

    # act
    result = service.get_user_data(user_profile)

    # assert
    assert result['email'] == 'test@example.com'
    assert result['first_name'] == 'Test'
    assert result['last_name'] == 'User'
    assert result['photo'] == 'https://example.com/photo.jpg'

    capture_sentry_mock.assert_called_once()


def test_get_user_data__not_first_name__set_default(mocker):
    # arrange
    user_profile = {
        'sub': 'auth0|123456',
        'email': 'test@example.com',
        'name': 'Test User Full Name'
    }
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message'
    )
    service = Auth0Service()

    # act
    result = service.get_user_data(user_profile)

    # assert
    assert result['first_name'] == 'Test'
    assert result['last_name'] == 'User Full Name'
    capture_sentry_mock.assert_called_once()


def test_get_user_data__email_not_found__raise_exception():
    # arrange
    user_profile = {
        'sub': 'auth0|123456',
        'given_name': 'Test',
        'family_name': 'User'
    }
    service = Auth0Service()

    # act & assert
    with pytest.raises(exceptions.EmailNotExist):
        service.get_user_data(user_profile)


def test_get_first_access_token__ok(mocker):

    # arrange
    state = 'ASDSDasd12'
    auth_response = {'code': 'test_code', 'state': state}
    domain = 'test_client_domain'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    redirect_uri = 'test_redirect_uri'
    response_data = {
        'access_token': 'test_access_token',
        'refresh_token': 'test_refresh_token',
        'token_type': 'Bearer',
        'expires_in': 3600
    }
    response_mock = Mock(ok=True)
    response_mock.json.return_value = response_data
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.post',
        return_value=response_mock
    )
    get_cache_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_cache',
        return_value=True
    )
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings',
    )
    settings_mock.AUTH0_DOMAIN = domain
    settings_mock.AUTH0_CLIENT_ID = client_id
    settings_mock.AUTH0_CLIENT_SECRET = client_secret
    settings_mock.AUTH0_REDIRECT_URI = redirect_uri
    service = Auth0Service()

    # act
    result = service._get_first_access_token(auth_response)

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
        timeout=10
    )


def test_get_first_access_token__clear_cache__raise_exception(mocker):

    # arrange
    state = 'ASDSDasd12'
    auth_response = {'code': 'test_code', 'state': state}
    get_cache_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_cache',
        return_value=None
    )
    service = Auth0Service()

    # act & assert
    with pytest.raises(exceptions.TokenInvalidOrExpired):
        service._get_first_access_token(auth_response)

    get_cache_mock.assert_called_once_with(key=state)


def test_get_first_access_token__request_return_error__raise_exception(mocker):

    # arrange
    state = 'ASDSDasd12'
    auth_response = {'code': 'test_code', 'state': state}
    domain = 'test_client_domain'
    response_content_mock = b'Error content'
    response_mock = Mock(ok=False)
    response_mock.content = response_content_mock
    response_mock.raise_for_status.side_effect = requests.RequestException(
        'HTTP Error'
    )
    response_mock.json.return_value = {
        'error': 'invalid_grant',
        'access_token': 'fake_token'
    }
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.post',
        return_value=response_mock,
    )
    get_cache_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_cache',
        return_value=True
    )
    sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message'
    )
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings',
    )
    settings_mock.AUTH0_DOMAIN = domain
    service = Auth0Service()

    # act & assert
    with pytest.raises(exceptions.TokenInvalidOrExpired):
        service._get_first_access_token(auth_response)

    get_cache_mock.assert_called_once_with(key=state)
    request_mock.assert_called_once()
    sentry_mock.assert_called_once_with(
        message='Get Auth0 access token return an error: HTTP Error',
        level=SentryLogLevel.ERROR
    )


def test_get_user_profile__ok(mocker):

    # arrange
    access_token = 'Q@#!@adad123'
    domain = 'test_client_domain'
    response_data = {
        'sub': 'auth0|123456',
        'email': 'test@example.com',
        'given_name': 'Test',
        'family_name': 'User'
    }
    response_mock = Mock(ok=True)
    response_mock.json.return_value = response_data
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.get',
        return_value=response_mock,
    )
    mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_cache',
        return_value=None
    )
    set_cache_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._set_cache'
    )
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings',
    )
    settings_mock.AUTH0_DOMAIN = domain
    service = Auth0Service()

    # act
    result = service._get_user_profile(access_token)

    # assert
    assert result == response_data

    request_mock.assert_called_once_with(
        f'https://{domain}/userinfo',
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=10
    )
    set_cache_mock.assert_called_once_with(
        value=response_data, key=f'user_profile_{access_token}'
    )


def test_get_user_profile__response_error__raise_exception(mocker):

    # arrange
    response_content_mock = b'Error content'
    response_mock = Mock(ok=False)
    response_mock.content = response_content_mock
    response_mock.raise_for_status.side_effect = requests.RequestException(
        'HTTP Error'
    )
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.get',
        return_value=response_mock,
    )
    access_token = 'Q@#!@adad123'
    domain = 'test_client_domain'
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings',
    )
    sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message'
    )
    get_cache_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_cache',
        return_value=None
    )
    mocker.patch(
        'src.authentication.services.auth0.Auth0Service._set_cache'
    )
    settings_mock.AUTH0_DOMAIN = domain
    service = Auth0Service()

    # act & assert
    with pytest.raises(exceptions.TokenInvalidOrExpired) as ex:
        service._get_user_profile(access_token)

    assert ex.value.message == MSG_AU_0009
    get_cache_mock.assert_called_once_with(key=f'user_profile_{access_token}')
    request_mock.assert_called_once_with(
        f'https://{domain}/userinfo',
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=10
    )
    sentry_mock.assert_called_once_with(
        message='Auth0 user profile request failed: HTTP Error',
        level=SentryLogLevel.ERROR
    )


def test_save_tokens_for_user__create__ok():

    # arrange
    user = create_test_user()
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
    service = Auth0Service()
    service.tokens = tokens_data

    # act
    service.save_tokens_for_user(user)

    # assert
    token = AccessToken.objects.get(
        user=user,
        source=SourceType.AUTH0
    )
    assert token.access_token == access_token
    assert token.refresh_token == refresh_token
    assert token.expires_in == expires_in


def test_save_tokens_for_user__update__ok():
    # arrange
    user = create_test_user()
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
    service = Auth0Service()
    service.tokens = new_tokens_data

    # act
    service.save_tokens_for_user(user)

    # assert
    token.refresh_from_db()
    assert token.access_token == new_tokens_data['access_token']
    assert token.refresh_token == new_tokens_data['refresh_token']
    assert token.expires_in == new_tokens_data['expires_in']


def test_save_tokens_for_user__unit_test__ok(mocker):
    # arrange
    user = create_test_user()
    tokens_data = {
        'refresh_token': 'some refresh',
        'access_token': 'some access',
        'token_type': 'Bearer',
        'expires_in': 300,
    }
    service = Auth0Service()
    service.tokens = tokens_data
    update_or_create_mock = mocker.patch(
        'src.authentication.models.AccessToken.objects.update_or_create'
    )

    # act
    service.save_tokens_for_user(user)

    # assert
    update_or_create_mock.assert_called_once_with(
        source=SourceType.AUTH0,
        user=user,
        defaults={
            'expires_in': 300,
            'refresh_token': 'some refresh',
            'access_token': 'some access',
        }
    )


def test_get_access_token__not_expired__ok():
    # arrange
    user = create_test_user()
    AccessToken.objects.create(
        user=user,
        source=SourceType.AUTH0,
        refresh_token='refresh_token_123',
        access_token='access_token_456',
        expires_in=3600
    )
    service = Auth0Service()

    # act
    result = service._get_access_token(user.id)

    # assert
    assert result == 'access_token_456'


def test_get_access_token__not_found__raise_exception(mocker):
    # arrange
    user = create_test_user()
    sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message'
    )

    service = Auth0Service()

    # act & assert
    with pytest.raises(exceptions.AccessTokenNotFound):
        service._get_access_token(user.id)

    sentry_mock.assert_called_once()


def test_get_management_api_token__ok(mocker):
    # arrange
    domain = 'test_client_domain'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    access_token = 'mgmt_access_token_123'
    response_data = {
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': 86400
    }
    response_mock = Mock()
    response_mock.raise_for_status = Mock()
    response_mock.json.return_value = response_data
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.post',
        return_value=response_mock
    )
    get_cache_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_cache',
        return_value=None
    )
    set_cache_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._set_cache'
    )
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings'
    )
    settings_mock.AUTH0_DOMAIN = domain
    settings_mock.AUTH0_CLIENT_ID = client_id
    settings_mock.AUTH0_CLIENT_SECRET = client_secret
    service = Auth0Service()

    # act
    result = service._get_management_api_token()

    # assert
    assert result == access_token
    get_cache_mock.assert_called_once_with(key=service.MGMT_TOKEN_CACHE_KEY)
    request_mock.assert_called_once_with(
        f'https://{domain}/oauth/token',
        json={
            'client_id': client_id,
            'client_secret': client_secret,
            'audience': f'https://{domain}/api/v2/',
            'grant_type': 'client_credentials'
        },
        timeout=10
    )
    set_cache_mock.assert_called_once_with(
        value=access_token, key=service.MGMT_TOKEN_CACHE_KEY
    )


def test_get_management_api_token__cached__ok(mocker):
    # arrange
    cached_token = 'cached_mgmt_token_456'
    get_cache_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_cache',
        return_value=cached_token
    )
    service = Auth0Service()

    # act
    result = service._get_management_api_token()

    # assert
    assert result == cached_token
    get_cache_mock.assert_called_once_with(key=service.MGMT_TOKEN_CACHE_KEY)


def test_get_users__ok(mocker):
    # arrange
    org_id = 'org_123'
    access_token = 'mgmt_token_456'
    domain = 'test_domain'
    members_data = [
        {'user_id': 'user1', 'email': 'user1@example.com'},
        {'user_id': 'user2', 'email': 'user2@example.com'}
    ]
    response_mock = Mock()
    response_mock.raise_for_status = Mock()
    response_mock.json.return_value = members_data
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.get',
        return_value=response_mock
    )
    get_mgmt_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_management_api_token',
        return_value=access_token
    )
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings'
    )
    settings_mock.AUTH0_DOMAIN = domain
    service = Auth0Service()

    # act
    result = service._get_users(org_id)

    # assert
    assert result == members_data
    get_mgmt_token_mock.assert_called_once()
    request_mock.assert_called_once_with(
        f'https://{domain}/api/v2/organizations/{org_id}/members',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        },
        timeout=10
    )


def test_private_get_user_organizations__ok(mocker):
    # arrange
    user_id = 'auth0|123456'
    access_token = 'mgmt_token_456'
    domain = 'test_domain'
    organizations_data = [
        {'id': 'org_123', 'name': 'Test Org 1'},
        {'id': 'org_456', 'name': 'Test Org 2'}
    ]
    response_mock = Mock()
    response_mock.raise_for_status = Mock()
    response_mock.json.return_value = organizations_data
    mocker.patch(
        'src.authentication.services.auth0.requests.get',
        return_value=response_mock
    )
    mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_management_api_token',
        return_value=access_token
    )
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings'
    )
    settings_mock.AUTH0_DOMAIN = domain
    service = Auth0Service()

    # act
    result = service._get_user_organizations(user_id)

    # assert
    assert result == organizations_data


def test_update_user_contacts__ok(mocker):
    # arrange
    user = create_test_user()
    access_token = 'test_access_token'
    user_profile = {
        'sub': 'auth0|123456',
        'email': 'test@example.com'
    }
    organizations = [{'id': 'org_123'}]
    members_data = [{
        'email': 'contact@example.com',
        'given_name': 'John',
        'family_name': 'Doe',
        'picture': 'https://example.com/photo.jpg',
        'user_id': 'auth0|789'
    }]
    mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_access_token',
        return_value=access_token
    )
    mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_user_profile',
        return_value=user_profile
    )
    mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_organizations',
        return_value=organizations
    )
    mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_users',
        return_value=members_data
    )
    mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message'
    )
    service = Auth0Service()

    # act
    result = service.update_user_contacts(user)

    # assert
    assert 'created_contacts' in result
    assert 'updated_contacts' in result
    contact = Contact.objects.get(email='contact@example.com')
    assert contact.first_name == 'John'
    assert contact.last_name == 'Doe'
    assert contact.photo == 'https://example.com/photo.jpg'


def test_update_user_contacts__exception__not_handled(mocker):
    # arrange
    user = create_test_user()
    get_access_token_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_access_token',
        side_effect=Exception('API Error')
    )
    service = Auth0Service()

    # act & assert
    with pytest.raises(Exception, match='API Error'):
        service.update_user_contacts(user)

    get_access_token_mock.assert_called_once_with(user.id)


def test_update_user_contacts__full_flow__ok(mocker):
    # arrange
    user = create_test_user()
    access_token = 'test_access_token'
    user_profile = {
        'sub': 'auth0|123456',
        'email': 'test@example.com'
    }
    organizations = [{'id': 'org_123'}]
    members_data = [{
        'email': 'contact@example.com',
        'given_name': 'John',
        'family_name': 'Doe',
        'picture': 'https://example.com/photo.jpg',
        'user_id': 'auth0|789'
    }]

    mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_access_token',
        return_value=access_token
    )
    mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_user_profile',
        return_value=user_profile
    )
    mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_organizations',
        return_value=organizations
    )
    mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_users',
        return_value=members_data
    )
    mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message'
    )
    service = Auth0Service()

    # act
    result = service.update_user_contacts(user)

    # assert
    assert result['created_contacts'] == ['contact@example.com']
    assert result['updated_contacts'] == []


def test_authenticate_user__existing_user__ok(mocker):
    # arrange
    user = create_test_user(email='test@example.com')
    token = 'test_token'
    access_token = 'auth0_access_token'
    auth_response = {'code': 'test_code', 'state': 'test_state'}
    user_profile = {
        'sub': 'auth0|123456',
        'email': 'test@example.com',
        'given_name': 'Test',
        'family_name': 'User'
    }
    user_data = {
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User'
    }
    request_mock = Mock()
    request_mock.headers.get.return_value = 'Test-Agent'
    request_mock.META.get.return_value = '127.0.0.1'
    get_first_access_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_first_access_token',
        return_value=access_token
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_user_profile',
        return_value=user_profile
    )
    get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.get_user_data',
        return_value=user_data
    )
    mocker.patch(
        'src.authentication.services.AuthService.get_auth_token',
        return_value=token
    )
    user_get_mock = mocker.patch(
        'src.authentication.services.auth0.UserModel.objects.active'
    )
    user_get_mock.return_value.get.return_value = user
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.save_tokens_for_user'
    )

    service = Auth0Service(request=request_mock)

    # act
    result_user, result_token = service.authenticate_user(auth_response)

    # assert
    assert result_user == user
    assert result_token == token

    get_first_access_token_mock.assert_called_once_with(auth_response)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_data_mock.assert_called_once_with(user_profile)
    user_get_mock.return_value.get.assert_called_once_with(
        email='test@example.com'
    )
    save_tokens_mock.assert_called_once_with(user)


def test_authenticate_user__new_user_signup_disabled__raise_exception(mocker):
    # arrange
    auth_response = {'code': 'test_code', 'state': 'test_state'}
    access_token = 'test_access_token'
    user_profile = {
        'sub': 'auth0|123456',
        'email': 'newuser@example.com',
        'given_name': 'New',
        'family_name': 'User'
    }
    user_data = {
        'email': 'newuser@example.com',
        'first_name': 'New',
        'last_name': 'User'
    }
    request_mock = Mock()
    get_first_access_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_first_access_token',
        return_value=access_token
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_user_profile',
        return_value=user_profile
    )
    get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.get_user_data',
        return_value=user_data
    )
    user_get_mock = mocker.patch(
        'src.authentication.services.auth0.UserModel.objects.active'
    )
    user_get_mock.return_value.get.side_effect = UserModel.DoesNotExist()
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings'
    )
    settings_mock.PROJECT_CONF = {'SIGNUP': False}
    service = Auth0Service(request=request_mock)

    # act & assert
    with pytest.raises(AuthenticationFailed):
        service.authenticate_user(auth_response)

    get_first_access_token_mock.assert_called_once_with(auth_response)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_data_mock.assert_called_once_with(user_profile)


def test_authenticate_user__new_user_create_account__ok(mocker):
    # arrange
    user = create_test_user(email='newuser@example.com')
    token = 'test_token'
    access_token = 'test_access_token'
    auth_response = {'code': 'test_code', 'state': 'test_state'}
    user_profile = {
        'sub': 'auth0|123456',
        'email': 'newuser@example.com',
        'given_name': 'New',
        'family_name': 'User',
        'picture': None
    }
    organizations = [{'id': 'org_123', 'name': 'Test Org'}]
    request_mock = Mock()
    get_first_access_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_first_access_token',
        return_value=access_token
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_user_profile',
        return_value=user_profile
    )
    get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.get_user_data',
        return_value={
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'job_title': None,
            'photo': None,
            'company_name': None
        }
    )
    get_user_organizations_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_organizations',
        return_value=organizations
    )
    user_get_mock = mocker.patch(
        'src.authentication.services.auth0.UserModel.objects.active'
    )
    user_get_mock.return_value.get.side_effect = UserModel.DoesNotExist()
    account_filter_mock = mocker.patch(
        'src.accounts.models.Account.objects.filter'
    )
    account_filter_mock.return_value.first.return_value = None
    signup_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.signup',
        return_value=(user, token)
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.save_tokens_for_user'
    )
    log_service_instance_mock = Mock()
    mocker.patch(
        'src.authentication.services.auth0.AccountLogService',
        return_value=log_service_instance_mock
    )
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings'
    )
    settings_mock.PROJECT_CONF = {'SIGNUP': True}

    service = Auth0Service(request=request_mock)
    service.tokens = {'access_token': 'test_token'}

    # act
    result_user, result_token = service.authenticate_user(auth_response)

    # assert
    assert result_user == user
    assert result_token == token
    get_first_access_token_mock.assert_called_once_with(auth_response)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_data_mock.assert_called_once_with(user_profile)
    get_user_organizations_mock.assert_called_once_with('auth0|123456')
    signup_mock.assert_called_once()
    save_tokens_mock.assert_called_once_with(user)


def test_authenticate_user__join_existing_account__ok(mocker):
    # arrange
    user = create_test_user(email='newuser@example.com')
    token = 'test_token'
    access_token = 'test_access_token'
    auth_response = {'code': 'test_code', 'state': 'test_state'}
    user_profile = {
        'sub': 'auth0|123456',
        'email': 'newuser@example.com',
        'given_name': 'New',
        'family_name': 'User'
    }
    organizations = [{'id': 'org_123', 'name': 'Test Org'}]
    existing_account = Account.objects.create(
        name='Existing Account',
        external_id='org_123'
    )
    request_mock = Mock()

    get_first_access_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_first_access_token',
        return_value=access_token
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service._get_user_profile',
        return_value=user_profile
    )
    get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.get_user_data',
        return_value={
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'job_title': None,
            'photo': None,
            'company_name': None
        }
    )
    get_user_organizations_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_organizations',
        return_value=organizations
    )
    user_get_mock = mocker.patch(
        'src.authentication.services.auth0.UserModel.objects.active'
    )
    user_get_mock.return_value.get.side_effect = UserModel.DoesNotExist()
    account_filter_mock = mocker.patch(
        'src.accounts.models.Account.objects.filter'
    )
    account_filter_mock.return_value.first.return_value = existing_account
    join_existing_account_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.join_existing_account',
        return_value=(user, token)
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.Auth0Service.save_tokens_for_user'
    )
    log_service_instance_mock = Mock()
    mocker.patch(
        'src.authentication.services.auth0.AccountLogService',
        return_value=log_service_instance_mock
    )
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings'
    )
    settings_mock.PROJECT_CONF = {'SIGNUP': True}
    service = Auth0Service(request=request_mock)
    service.tokens = {'access_token': 'test_token'}

    # act
    result_user, result_token = service.authenticate_user(auth_response)

    # assert
    assert result_user == user
    assert result_token == token
    get_first_access_token_mock.assert_called_once_with(auth_response)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_data_mock.assert_called_once_with(user_profile)
    get_user_organizations_mock.assert_called_once_with('auth0|123456')
    join_existing_account_mock.assert_called_once_with(
        account=existing_account,
        email='newuser@example.com',
        first_name='New',
        last_name='User',
        job_title=None,
        photo=None,
        company_name=None
    )
    save_tokens_mock.assert_called_once_with(user)
