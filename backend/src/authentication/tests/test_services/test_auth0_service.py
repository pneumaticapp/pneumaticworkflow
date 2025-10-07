import pytest
from src.authentication import messages
from src.accounts.enums import SourceType
from src.authentication.models import AccessToken
from src.authentication.services import exceptions
from src.authentication.services.auth0 import Auth0Service
from src.processes.tests.fixtures import create_test_user
from src.utils.logging import SentryLogLevel


pytestmark = pytest.mark.django_db


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
    auth_response = mocker.Mock()
    service = Auth0Service()

    # act
    result = service.get_user_data(auth_response)

    # assert
    get_access_token_mock.assert_called_once_with(auth_response)
    get_user_mock.assert_called_once_with(access_token)
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


def test_save_tokens_for_user__create__ok(mocker):

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


def test_save_tokens_for_user__update__ok(mocker):

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
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None
    )
    expected_result = {
        'created_contacts': ['contact@example.com'],
        'updated_contacts': []
    }
    update_user_contacts_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.update_user_contacts',
        return_value=expected_result
    )
    service = Auth0Service()

    # act
    result = service.update_user_contacts(user)

    # assert
    assert result == expected_result
    auth0_service_init_mock.assert_called_once()
    update_user_contacts_mock.assert_called_once_with(user)


def test_update_user_contacts__exception__handle_gracefully(mocker):
    # arrange
    user = create_test_user()
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None
    )
    update_user_contacts_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.update_user_contacts',
        side_effect=Exception('API Error')
    )
    mocker.patch(
        'src.authentication.services.auth0.capture_sentry_message'
    )
    service = Auth0Service()

    # act
    with pytest.raises(Exception):
        service.update_user_contacts(user)

    # assert
    auth0_service_init_mock.assert_called_once()
    update_user_contacts_mock.assert_called_once_with(user)


def test_get_user_organizations__ok(mocker):
    # arrange
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None
    )
    user_data = {'sub': 'auth0|123456'}
    organizations = [
        {'id': 'org_123', 'name': 'Test Org 1'},
        {'id': 'org_456', 'name': 'Test Org 2'}
    ]
    get_user_organizations_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_organizations',
        return_value=organizations
    )
    service = Auth0Service()

    # act
    result = service.get_user_organizations(user_data)

    # assert
    assert result == organizations
    auth0_service_init_mock.assert_called_once()
    get_user_organizations_mock.assert_called_once_with(user_data)


def test_get_user_organizations__no_user_id__return_empty(mocker):
    # arrange
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None
    )
    user_data = {}
    get_user_organizations_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_organizations',
        return_value=[]
    )
    service = Auth0Service()

    # act
    result = service.get_user_organizations(user_data)

    # assert
    assert result == []
    auth0_service_init_mock.assert_called_once()
    get_user_organizations_mock.assert_called_once_with(user_data)


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


def test_get_user_organizations_private__ok(mocker):
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
