import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from src.authentication import messages
from src.accounts.enums import SourceType
from src.authentication.models import AccessToken
from src.authentication.services import exceptions
from src.authentication.services.auth0 import Auth0Service
from src.processes.tests.fixtures import create_test_user
from src.utils.logging import SentryLogLevel


pytestmark = pytest.mark.django_db
UserModel = get_user_model()


def test__get_auth_uri__ok(mocker):

    # arrange
    state = 'YrtkHpALzeTDnliK'
    get_state_mock = mocker.patch(
        'src.authentication.services.auth0.uuid4',
        return_value=state
    )
    set_cache_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._set_cache'
    )
    query_params = 'urlencoded-params'
    urlencode_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'requests.compat.urlencode',
        return_value=query_params
    )

    domain = 'test_client_domain'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    redirect_uri = 'https://some.redirect/uri'

    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings'
    )
    settings_mock.AUTH0_CLIENT_ID = client_id
    settings_mock.AUTH0_CLIENT_SECRET = client_secret
    settings_mock.AUTH0_DOMAIN = domain
    settings_mock.AUTH0_REDIRECT_URI = redirect_uri
    service = Auth0Service()

    # act
    result = service.get_auth_uri()

    # assert
    get_state_mock.assert_called_once()
    urlencode_mock.assert_called_once_with(
        {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': 'openid email profile offline_access',
            'state': state,
            'response_type': 'code',
        }
    )
    set_cache_mock.assert_called_once_with(
        value=True,
        key=state
    )
    assert result == f'https://{domain}/authorize?{query_params}'


def test_get_user_data__ok(mocker):

    # arrange
    access_token = '!@#!@#@!wqww23'
    get_access_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_first_access_token',
        return_value=access_token
    )
    email = 'test@test.test'
    first_name = 'Fa'
    last_name = 'Bio'
    photo_url = 'https://test.image.com'
    profile_data = {
        'email': email,
        'given_name': first_name,
        'family_name': last_name,
        'picture': photo_url
    }
    get_user_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_profile',
        return_value=profile_data
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message'
    )
    auth_response = mocker.Mock()
    service = Auth0Service()

    # act
    result = service.get_user_data(auth_response)

    # assert
    get_access_token_mock.assert_called_once_with(auth_response)
    get_user_mock.assert_called_once_with(access_token)
    capture_sentry_mock.assert_called_once_with(
        message=f'Auth0 user profile {email}',
        data={
            'photo': photo_url,
            'first_name': first_name,
            'user_profile': profile_data,
            'email': email,
        },
        level=SentryLogLevel.INFO
    )
    assert result['email'] == email
    assert result['first_name'] == first_name
    assert result['last_name'] == last_name
    assert result['company_name'] is None
    assert result['photo'] == photo_url
    assert result['job_title'] is None


def test_get_user_data__not_first_name__set_default(mocker):

    # arrange
    access_token = '!@#!@#@!wqww23'
    get_access_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_first_access_token',
        return_value=access_token
    )
    email = 'username@domain.com'
    first_name = None
    last_name = 'Bio'
    photo_url = 'https://test.image.com'
    profile_data = {
        'email': email,
        'given_name': first_name,
        'family_name': last_name,
        'picture': photo_url
    }
    get_user_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_profile',
        return_value=profile_data
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message'
    )
    auth_response = mocker.Mock()
    service = Auth0Service()

    # act
    result = service.get_user_data(auth_response)

    # assert
    get_access_token_mock.assert_called_once_with(auth_response)
    get_user_mock.assert_called_once_with(access_token)
    capture_sentry_mock.assert_called_once_with(
        message=f'Auth0 user profile {email}',
        data={
            'photo': photo_url,
            'first_name': 'username',
            'user_profile': profile_data,
            'email': email,
        },
        level=SentryLogLevel.INFO
    )
    assert result['first_name'] == 'username'


def test_get_user_data__email_not_found__raise_exception(mocker):

    # arrange
    access_token = '!@#!@#@!wqww23'
    get_access_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_first_access_token',
        return_value=access_token
    )
    email = 'test@test.test'
    first_name = 'Fa'
    last_name = 'Bio'
    photo_url = 'https://test.image.com'
    profile_data = {
        'email': email,
        'given_name': first_name,
        'family_name': last_name,
        'picture': photo_url
    }
    get_user_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_profile',
        return_value=profile_data
    )
    auth_response = mocker.Mock()
    service = Auth0Service()

    # act
    result = service.get_user_data(auth_response)

    # assert
    get_access_token_mock.assert_called_once_with(auth_response)
    get_user_mock.assert_called_once_with(access_token)
    assert result['email'] == email
    assert result['first_name'] == first_name
    assert result['last_name'] == last_name
    assert result['company_name'] is None
    assert result['photo'] == photo_url
    assert result['job_title'] is None


def test_get_first_access_token__ok(mocker):

    # arrange
    state = 'ASDSDasd12'
    code = 'some code'
    auth_response = {'state': state, 'code': code}
    cache_value = True
    get_cache_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_cache',
        return_value=cache_value
    )
    response = {
        'token_type': 'Bearer',
        'access_token': '!@#wad123'
    }
    response_mock = mocker.Mock(
        json=mocker.Mock(return_value=response)
    )
    request_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'requests.post',
        return_value=response_mock
    )

    domain = 'test_client_domain'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    redirect_uri = 'https://some.redirect/uri'
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings'
    )
    settings_mock.AUTH0_CLIENT_ID = client_id
    settings_mock.AUTH0_CLIENT_SECRET = client_secret
    settings_mock.AUTH0_DOMAIN = domain
    settings_mock.AUTH0_REDIRECT_URI = redirect_uri
    service = Auth0Service()

    # act
    result = service._get_first_access_token(auth_response)

    # assert
    assert result == response["access_token"]
    assert service.tokens == response
    get_cache_mock.assert_called_once_with(key=state)
    request_mock.assert_called_once_with(
        f'https://{domain}/oauth/token',
        data={
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
        }
    )


def test_get_first_access_token__clear_cache__raise_exception(mocker):

    # arrange
    state = 'ASDSDasd12'
    code = 'some code'
    auth_response = {'state': state, 'code': code}
    get_cache_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_cache',
        return_value=None
    )
    response = {
        'token_type': 'Bearer',
        'access_token': '!@#wad123'
    }
    response_mock = mocker.Mock(
        json=mocker.Mock(return_value=response)
    )
    request_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'requests.post',
        return_value=response_mock
    )

    service = Auth0Service()

    # act
    with pytest.raises(exceptions.TokenInvalidOrExpired) as ex:
        service._get_first_access_token(auth_response)

    # assert
    assert ex.value.message == messages.MSG_AU_0009
    get_cache_mock.assert_called_once_with(key=state)
    request_mock.assert_not_called()


def test_get_first_access_token__request_return_error__raise_exception(mocker):

    # arrange
    state = 'ASDSDasd12'
    code = 'some code'
    auth_response = {'state': state, 'code': code}
    get_cache_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_cache',
        return_value=True
    )
    response_data = {
        'token_type': 'Bearer',
        'access_token': '!@#wad123'
    }
    response_mock = mocker.Mock(ok=False)
    response_content_mock = mocker.Mock()
    response_mock.json = mocker.Mock(return_value=response_data)
    response_mock.content = response_content_mock
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.post',
        return_value=response_mock
    )
    sentry_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'capture_sentry_message'
    )
    domain = 'test_client_domain'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    redirect_uri = 'https://some.redirect/uri'
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings'
    )
    settings_mock.AUTH0_CLIENT_ID = client_id
    settings_mock.AUTH0_CLIENT_SECRET = client_secret
    settings_mock.AUTH0_DOMAIN = domain
    settings_mock.AUTH0_REDIRECT_URI = redirect_uri

    service = Auth0Service()

    # act
    with pytest.raises(exceptions.TokenInvalidOrExpired) as ex:
        service._get_first_access_token(auth_response)

    # assert
    assert ex.value.message == messages.MSG_AU_0009
    get_cache_mock.assert_called_once_with(key=state)
    request_mock.assert_called_once_with(
        f'https://{domain}/oauth/token',
        data={
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
        }
    )
    sentry_mock.assert_called_once_with(
        message='Get Auth0 access token return an error',
        data={'content': response_content_mock},
        level=SentryLogLevel.ERROR
    )


def test_get_user_profile__ok(mocker):

    # arrange
    response_data = mocker.Mock()
    response_mock = mocker.Mock(ok=True)
    response_mock.json = mocker.Mock(return_value=response_data)
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.get',
        return_value=response_mock
    )
    access_token = 'Q@#!@adad123'
    domain = 'test_client_domain'
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings'
    )
    settings_mock.AUTH0_DOMAIN = domain
    service = Auth0Service()

    # act
    result = service._get_user_profile(access_token)

    # assert
    assert result == response_data
    request_mock.assert_called_once_with(
        f'https://{domain}/userinfo',
        headers={'Authorization': f'Bearer {access_token}'}
    )


def test_get_user_profile__response_error__raise_exception(mocker):

    # arrange
    response_data = mocker.Mock()
    response_content_mock = mocker.Mock()
    response_mock = mocker.Mock(ok=False)
    response_mock.json = mocker.Mock(return_value=response_data)
    response_mock.content = response_content_mock
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.get',
        return_value=response_mock
    )
    access_token = 'Q@#!@adad123'
    domain = 'test_client_domain'
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings'
    )
    sentry_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'capture_sentry_message'
    )
    settings_mock.AUTH0_DOMAIN = domain
    service = Auth0Service()

    # act
    with pytest.raises(exceptions.TokenInvalidOrExpired) as ex:
        service._get_user_profile(access_token)

    # assert
    assert ex.value.message == messages.MSG_AU_0009
    request_mock.assert_called_once_with(
        f'https://{domain}/userinfo',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    sentry_mock.assert_called_once_with(
        message='Get Auth0 user profile return an error',
        data={'content': response_content_mock},
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
    assert AccessToken.objects.get(
        source=SourceType.AUTH0,
        user=user,
        refresh_token=refresh_token,
        access_token=access_token,
        expires_in=expires_in,
    )


def test_save_tokens_for_user__update__ok():

    # arrange
    user = create_test_user()
    token_type = 'Bearer'
    token = AccessToken.objects.create(
        source=SourceType.AUTH0,
        user=user,
        refresh_token='ahsdsdasd23ggfn',
        access_token=f'{token_type} !@#asas',
        expires_in=360
    )
    new_tokens_data = {
        'refresh_token': 'new refresh',
        'access_token': 'new access token',
        'token_type': token_type,
        'expires_in': 400
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


def test_get_access_token__not_expired__ok(mocker):
    # arrange
    user = create_test_user()
    token = AccessToken.objects.create(
        user=user,
        source=SourceType.AUTH0,
        access_token='test_access_token',
        refresh_token='test_refresh_token',
        expires_in=3600
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None
    )
    service = Auth0Service()

    # act
    result = service._get_access_token(user.id)

    # assert
    assert result == token.access_token
    auth0_service_init_mock.assert_called_once()


def test_get_access_token__not_found__raise_exception(mocker):
    # arrange
    user = create_test_user()
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message'
    )
    service = Auth0Service()

    # act
    with pytest.raises(exceptions.AccessTokenNotFound):
        service._get_access_token(user.id)

    # assert
    auth0_service_init_mock.assert_called_once()
    capture_sentry_mock.assert_called_once_with(
        message='Auth0 Access token not found for the user',
        data={'user_id': user.id},
        level=SentryLogLevel.ERROR
    )


def test_update_user_contacts__ok(mocker):
    # arrange
    user = create_test_user()
    access_token = 'test_access_token'
    user_profile = {'sub': 'auth0|123456'}
    organizations = [{'id': 'org_123'}]
    members_data = [
        {
            'email': 'contact@example.com',
            'given_name': 'John',
            'family_name': 'Doe',
            'picture': 'https://example.com/photo.jpg',
            'job_title': 'Developer',
            'user_id': 'auth0|789'
        }
    ]

    get_access_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_access_token',
        return_value=access_token
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_profile',
        return_value=user_profile
    )
    get_user_organizations_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_organizations',
        return_value=organizations
    )
    get_users_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_users',
        return_value=members_data
    )
    contact_create_mock = mocker.patch(
        'src.accounts.models.Contact.objects.update_or_create',
        return_value=(mocker.Mock(), True)
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message'
    )

    service = Auth0Service()

    # act
    result = service.update_user_contacts(user)

    # assert
    assert result['created_contacts'] == ['contact@example.com']
    assert result['updated_contacts'] == []
    get_access_token_mock.assert_called_once_with(user.id)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_organizations_mock.assert_called_once_with('auth0|123456')
    get_users_mock.assert_called_once_with('org_123')
    contact_create_mock.assert_called_once_with(
        account=user.account,
        user=user,
        source=SourceType.AUTH0,
        email='contact@example.com',
        defaults={
            'photo': 'https://example.com/photo.jpg',
            'first_name': 'John',
            'last_name': 'Doe',
            'job_title': 'Developer',
            'source_id': 'auth0|789',
        }
    )
    capture_sentry_mock.assert_not_called()


def test_update_user_contacts__exception__handle_gracefully(mocker):
    # arrange
    user = create_test_user()
    access_token = 'test_access_token'

    get_access_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_access_token',
        return_value=access_token
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_profile',
        side_effect=Exception('API Error')
    )
    get_user_organizations_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_organizations'
    )
    get_users_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_users'
    )
    contact_create_mock = mocker.patch(
        'src.accounts.models.Contact.objects.update_or_create'
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message'
    )

    service = Auth0Service()

    # act
    result = service.update_user_contacts(user)

    # assert
    assert result == {'created_contacts': [], 'updated_contacts': []}
    get_access_token_mock.assert_called_once_with(user.id)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_organizations_mock.assert_not_called()
    get_users_mock.assert_not_called()
    contact_create_mock.assert_not_called()
    capture_sentry_mock.assert_called_once_with(
        message=f'Auth0 contacts update failed: API Error',
        data={'user_id': user.id, 'user_email': user.email},
        level=SentryLogLevel.ERROR
    )


def test_get_management_api_token__ok(mocker):
    # arrange
    get_cache_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_cache',
        return_value=None
    )
    access_token = 'mgmt_access_token_123'
    response_data = {
        'access_token': access_token,
        'expires_in': 3600
    }
    response_mock = mocker.Mock()
    response_mock.raise_for_status = mocker.Mock()
    response_mock.json = mocker.Mock(return_value=response_data)
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.post',
        return_value=response_mock
    )
    set_cache_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._set_cache'
    )
    domain = 'test_domain'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
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
    get_cache_mock.assert_called_once_with(service.MGMT_TOKEN_CACHE_KEY)
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
        service.MGMT_TOKEN_CACHE_KEY,
        access_token
    )


def test_get_management_api_token__cached__ok(mocker):
    # arrange
    cached_token = 'cached_mgmt_token_456'
    get_cache_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_cache',
        return_value=cached_token
    )
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.post'
    )
    service = Auth0Service()

    # act
    result = service._get_management_api_token()

    # assert
    assert result == cached_token
    get_cache_mock.assert_called_once_with(service.MGMT_TOKEN_CACHE_KEY)
    request_mock.assert_not_called()


def test_get_users__ok(mocker):
    # arrange
    org_id = 'org_123'
    access_token = 'mgmt_token_789'
    get_mgmt_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_management_api_token',
        return_value=access_token
    )
    members_data = [
        {'email': 'user1@test.com', 'name': 'User One'},
        {'email': 'user2@test.com', 'name': 'User Two'}
    ]
    response_mock = mocker.Mock()
    response_mock.raise_for_status = mocker.Mock()
    response_mock.json = mocker.Mock(return_value=members_data)
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.get',
        return_value=response_mock
    )
    domain = 'test_domain'
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
    access_token = 'mgmt_token_789'
    get_mgmt_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_management_api_token',
        return_value=access_token
    )
    orgs_data = [
        {'id': 'org_123', 'name': 'Test Org 1'},
        {'id': 'org_456', 'name': 'Test Org 2'}
    ]
    response_mock = mocker.Mock()
    response_mock.raise_for_status = mocker.Mock()
    response_mock.json = mocker.Mock(return_value=orgs_data)
    request_mock = mocker.patch(
        'src.authentication.services.auth0.requests.get',
        return_value=response_mock
    )
    domain = 'test_domain'
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings'
    )
    settings_mock.AUTH0_DOMAIN = domain
    service = Auth0Service()

    # act
    result = service._get_user_organizations(user_id)

    # assert
    assert result == orgs_data
    get_mgmt_token_mock.assert_called_once()
    request_mock.assert_called_once_with(
        f'https://{domain}/api/v2/users/{user_id}/organizations',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        },
        timeout=10
    )


def test_update_user_contacts__full_flow__ok(mocker):
    # arrange
    user = create_test_user()
    access_token = 'test_access_token'
    user_profile = {'sub': 'auth0|123456'}
    organizations = [{'id': 'org_123'}]
    members_data = [
        {
            'email': 'contact@example.com',
            'given_name': 'John',
            'family_name': 'Doe',
            'picture': 'https://example.com/photo.jpg',
            'job_title': 'Developer',
            'user_id': 'auth0|789'
        }
    ]

    get_access_token_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_access_token',
        return_value=access_token
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_profile',
        return_value=user_profile
    )
    get_user_organizations_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_organizations',
        return_value=organizations
    )
    get_users_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_users',
        return_value=members_data
    )
    contact_create_mock = mocker.patch(
        'src.accounts.models.Contact.objects.update_or_create',
        return_value=(mocker.Mock(), True)
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message'
    )

    service = Auth0Service()

    # act
    result = service.update_user_contacts(user)

    # assert
    assert result['created_contacts'] == ['contact@example.com']
    assert result['updated_contacts'] == []
    get_access_token_mock.assert_called_once_with(user.id)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_organizations_mock.assert_called_once_with('auth0|123456')
    get_users_mock.assert_called_once_with('org_123')
    contact_create_mock.assert_called_once()
    capture_sentry_mock.assert_not_called()


def test_authenticate_user__existing_user__ok(mocker):
    # arrange
    user = create_test_user(email='test@example.com')
    token = 'test_token'
    auth_response = {'code': 'test_code', 'state': 'test_state'}
    user_data = {
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User'
    }
    request_mock = mocker.Mock()
    request_mock.headers.get.return_value = 'Test-Agent'
    request_mock.META.get.return_value = '127.0.0.1'

    get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_data',
        return_value=user_data
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.AuthService.get_auth_token',
        return_value=token
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.save_tokens_for_user'
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_profile'
    )
    get_user_organizations_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_organizations'
    )
    account_filter_mock = mocker.patch(
        'src.accounts.models.Account.objects.filter'
    )
    join_existing_account_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.join_existing_account'
    )
    signup_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.signup'
    )
    log_service_instance_mock = mocker.Mock()
    log_service_mock = mocker.patch(
        'src.authentication.services.auth0.AccountLogService',
        return_value=log_service_instance_mock
    )
    mocker.patch(
        'src.authentication.services.auth0.settings'
    )

    service = Auth0Service(request=request_mock)

    # act
    result_user, result_token = service.authenticate_user(auth_response)

    # assert
    assert result_user == user
    assert result_token == token
    get_user_data_mock.assert_called_once_with(auth_response)
    get_auth_token_mock.assert_called_once_with(
        user=user,
        user_agent='Test-Agent',
        user_ip='127.0.0.1'
    )
    save_tokens_mock.assert_not_called()
    get_user_profile_mock.assert_not_called()
    get_user_organizations_mock.assert_not_called()
    account_filter_mock.assert_not_called()
    join_existing_account_mock.assert_not_called()
    signup_mock.assert_not_called()
    log_service_mock.assert_not_called()
    log_service_instance_mock.log_auth0.assert_not_called()


def test_authenticate_user__new_user_signup_disabled__raise_exception(mocker):
    # arrange
    auth_response = {'code': 'test_code', 'state': 'test_state'}
    user_data = {
        'email': 'newuser@example.com',
        'first_name': 'New',
        'last_name': 'User'
    }
    request_mock = mocker.Mock()

    get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_data',
        return_value=user_data
    )
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings'
    )
    settings_mock.PROJECT_CONF = {'SIGNUP': False}
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.AuthService.get_auth_token'
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_profile'
    )
    get_user_organizations_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_organizations'
    )
    account_filter_mock = mocker.patch(
        'src.accounts.models.Account.objects.filter'
    )
    join_existing_account_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.join_existing_account'
    )
    signup_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.signup'
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.save_tokens_for_user'
    )
    log_service_instance_mock = mocker.Mock()
    log_service_mock = mocker.patch(
        'src.authentication.services.auth0.AccountLogService',
        return_value=log_service_instance_mock
    )

    service = Auth0Service(request=request_mock)

    # act
    with pytest.raises(AuthenticationFailed):
        service.authenticate_user(auth_response)

    # assert
    get_user_data_mock.assert_called_once_with(auth_response)
    get_auth_token_mock.assert_not_called()
    get_user_profile_mock.assert_not_called()
    get_user_organizations_mock.assert_not_called()
    account_filter_mock.assert_not_called()
    join_existing_account_mock.assert_not_called()
    signup_mock.assert_not_called()
    save_tokens_mock.assert_not_called()
    log_service_mock.assert_not_called()
    log_service_instance_mock.log_auth0.assert_not_called()


def test_authenticate_user__new_user_create_account__ok(mocker):
    # arrange
    user = create_test_user(email='newuser@example.com')
    token = 'test_token'
    auth_response = {'code': 'test_code', 'state': 'test_state'}
    user_profile = {
        'sub': 'auth0|123456',
        'email': 'newuser@example.com',
        'given_name': 'New',
        'family_name': 'User',
        'picture': None
    }
    organizations = [{'id': 'org_123', 'name': 'Test Org'}]
    request_mock = mocker.Mock()

    get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_data',
        return_value={
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'job_title': None,
            'photo': None,
            'company_name': None
        }
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_profile',
        return_value=user_profile
    )
    get_user_organizations_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_organizations',
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
        'src.authentication.services.auth0.'
        'Auth0Service.signup',
        return_value=(user, token)
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.save_tokens_for_user'
    )
    log_service_instance_mock = mocker.Mock()
    log_service_mock = mocker.patch(
        'src.authentication.services.auth0.AccountLogService',
        return_value=log_service_instance_mock
    )
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings'
    )
    settings_mock.PROJECT_CONF = {'SIGNUP': True}
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.AuthService.get_auth_token',
        return_value=token
    )
    join_existing_account_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.join_existing_account'
    )

    service = Auth0Service(request=request_mock)
    service.tokens = {'access_token': 'test_token'}

    # act
    result_user, result_token = service.authenticate_user(auth_response)

    # assert
    assert result_user == user
    assert result_token == token
    get_user_data_mock.assert_called_once_with(auth_response)
    user_get_mock.return_value.get.assert_called_once_with(
        email='newuser@example.com'
    )
    get_user_profile_mock.assert_called_once_with('test_token')
    get_user_organizations_mock.assert_called_once_with(user_profile)
    account_filter_mock.assert_called_once_with(
        external_id__in=['org_123'],
        is_deleted=False
    )
    signup_mock.assert_called_once_with(
        email='newuser@example.com',
        first_name='New',
        last_name='User',
        job_title=None,
        photo=None,
        company_name=None,
        utm_source=None,
        utm_medium=None,
        utm_term=None,
        utm_content=None,
        utm_campaign=None,
        gclid=None
    )
    save_tokens_mock.assert_called_once_with(user)
    log_service_mock.assert_called_once_with(user)
    log_service_instance_mock.log_auth0.assert_called_once_with(
        title='Auth0 user created new account',
        data={
            'user_email': 'newuser@example.com',
            'account_id': user.account.id,
            'external_id': user.account.external_id,
            'organizations': organizations
        }
    )
    get_auth_token_mock.assert_not_called()
    join_existing_account_mock.assert_not_called()


def test_authenticate_user__join_existing_account__ok(mocker):
    # arrange
    user = create_test_user(email='newuser@example.com')
    existing_account = user.account
    existing_account.external_id = 'org_123'
    existing_account.save()

    token = 'test_token'
    auth_response = {'code': 'test_code', 'state': 'test_state'}
    user_profile = {
        'sub': 'auth0|123456',
        'email': 'newuser@example.com',
        'given_name': 'New',
        'family_name': 'User',
        'picture': None
    }
    organizations = [{'id': 'org_123', 'name': 'Test Org'}]
    request_mock = mocker.Mock()

    get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_data',
        return_value={
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'job_title': None,
            'photo': None,
            'company_name': None
        }
    )
    get_user_profile_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_profile',
        return_value=user_profile
    )
    get_user_organizations_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_organizations',
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
        'src.authentication.services.auth0.'
        'Auth0Service.join_existing_account',
        return_value=(user, token)
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.save_tokens_for_user'
    )
    log_service_instance_mock = mocker.Mock()
    log_service_mock = mocker.patch(
        'src.authentication.services.auth0.AccountLogService',
        return_value=log_service_instance_mock
    )
    settings_mock = mocker.patch(
        'src.authentication.services.auth0.settings'
    )
    settings_mock.PROJECT_CONF = {'SIGNUP': True}
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.AuthService.get_auth_token',
        return_value=token
    )
    signup_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.signup'
    )

    service = Auth0Service(request=request_mock)
    service.tokens = {'access_token': 'test_token'}

    # act
    result_user, result_token = service.authenticate_user(auth_response)

    # assert
    assert result_user == user
    assert result_token == token
    get_user_data_mock.assert_called_once_with(auth_response)
    user_get_mock.return_value.get.assert_called_once_with(
        email='newuser@example.com'
    )
    get_user_profile_mock.assert_called_once_with('test_token')
    get_user_organizations_mock.assert_called_once_with(user_profile)
    account_filter_mock.assert_called_once_with(
        external_id__in=['org_123'],
        is_deleted=False
    )
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
    log_service_mock.assert_called_once_with(user)
    log_service_instance_mock.log_auth0.assert_called_once_with(
        title='Auth0 user joined existing account',
        data={
            'user_email': 'newuser@example.com',
            'account_id': user.account.id,
            'external_id': user.account.external_id,
            'organizations': organizations
        }
    )
    get_auth_token_mock.assert_not_called()
    signup_mock.assert_not_called()
