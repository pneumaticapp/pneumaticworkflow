import pytest
from pneumatic_backend.authentication import messages
from pneumatic_backend.accounts.enums import (
    SourceType,
)
from pneumatic_backend.authentication.services.auth0 import (
    Auth0Service,
)
from pneumatic_backend.authentication.models import AccessToken
from pneumatic_backend.authentication.services import exceptions
from pneumatic_backend.utils.logging import SentryLogLevel
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
)


pytestmark = pytest.mark.django_db


def test__get_auth_uri__ok(mocker):

    # arrange
    state = 'YrtkHpALzeTDnliK'
    get_state_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.uuid4',
        return_value=state
    )
    set_cache_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
        'Auth0Service._set_cache'
    )
    query_params = 'urlencoded-params'
    urlencode_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
        'requests.compat.urlencode',
        return_value=query_params
    )

    domain = 'test_client_domain'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    redirect_uri = 'https://some.redirect/uri'

    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.settings'
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
            'scope': 'openid email profile',
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
        'pneumatic_backend.authentication.services.auth0.'
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
        'pneumatic_backend.authentication.services.auth0.'
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
        'pneumatic_backend.authentication.services.auth0.'
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
        'pneumatic_backend.authentication.services.auth0.'
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
        'pneumatic_backend.authentication.services.auth0.'
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
        'pneumatic_backend.authentication.services.auth0.'
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
        'pneumatic_backend.authentication.services.auth0.'
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
        'pneumatic_backend.authentication.services.auth0.'
        'requests.post',
        return_value=response_mock
    )

    domain = 'test_client_domain'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    redirect_uri = 'https://some.redirect/uri'
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.settings'
    )
    settings_mock.AUTH0_CLIENT_ID = client_id
    settings_mock.AUTH0_CLIENT_SECRET = client_secret
    settings_mock.AUTH0_DOMAIN = domain
    settings_mock.AUTH0_REDIRECT_URI = redirect_uri
    service = Auth0Service()

    # act
    result = service._get_first_access_token(auth_response)

    # assert
    assert result == f'{response["token_type"]} {response["access_token"]}'
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
        'pneumatic_backend.authentication.services.auth0.'
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
        'pneumatic_backend.authentication.services.auth0.'
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
        'pneumatic_backend.authentication.services.auth0.'
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
        'pneumatic_backend.authentication.services.auth0.requests.post',
        return_value=response_mock
    )
    sentry_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
        'capture_sentry_message'
    )
    domain = 'test_client_domain'
    client_id = 'test_client_id'
    client_secret = 'test_client_secret'
    redirect_uri = 'https://some.redirect/uri'
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.settings'
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
        'pneumatic_backend.authentication.services.auth0.requests.get',
        return_value=response_mock
    )
    access_token = 'Q@#!@adad123'
    domain = 'test_client_domain'
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.settings'
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
        'pneumatic_backend.authentication.services.auth0.requests.get',
        return_value=response_mock
    )
    access_token = 'Q@#!@adad123'
    domain = 'test_client_domain'
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.settings'
    )
    sentry_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
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
        access_token=f'{token_type} {access_token}',
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
    assert token.access_token == (
        f"{token_type} {new_tokens_data['access_token']}"
    )
    assert token.refresh_token == new_tokens_data['refresh_token']
    assert token.expires_in == new_tokens_data['expires_in']
