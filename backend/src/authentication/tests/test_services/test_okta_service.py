from unittest.mock import Mock

import base64
import pytest
import requests
from django.contrib.auth import get_user_model
from jwt import (
    DecodeError,
    InvalidTokenError,
)

from src.accounts.enums import (
    UserStatus,
    UserInviteStatus,
    SourceType,
)
from src.accounts.models import UserInvite
from src.authentication.messages import MSG_AU_0018
from src.authentication.models import (
    Account,
    AccessToken,
)
from src.authentication.services import exceptions
from src.authentication.services.okta import OktaService
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_account,
)
from src.utils.logging import SentryLogLevel

pytestmark = pytest.mark.django_db
UserModel = get_user_model()


def test_get_auth_uri__ok(mocker):
    # arrange
    domain = 'dev-123456.okta.com'
    client_id = 'test_client_id'
    redirect_uri = 'https://some.redirect/uri'
    state_uuid = 'YrtkHpALzeTDnliK'
    encrypted_domain = 'encrypted_domain_test'
    state = f"{state_uuid}{encrypted_domain}"

    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.OKTA_CLIENT_ID = client_id
    settings_mock.OKTA_REDIRECT_URI = redirect_uri
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
    set_cache_mock = mocker.patch(
        'src.authentication.services.okta.OktaService._set_cache',
    )
    mocker.patch(
        'src.authentication.services.okta.uuid4',
        return_value=state_uuid,
    )
    encrypt_mock = mocker.patch(
        'src.authentication.services.okta.OktaService.encrypt',
        return_value=encrypted_domain,
    )
    code_verifier_bytes = b'test_code_verifier_bytes_32_chars_long!!'
    code_verifier_encoded = base64.urlsafe_b64encode(
        code_verifier_bytes,
    ).decode('utf-8').rstrip('=')
    mocker.patch(
        'src.generics.mixins.services.secrets.token_bytes',
        return_value=code_verifier_bytes,
    )
    code_challenge_digest = b'test_digest'
    mocker.patch(
        'src.generics.mixins.services.hashlib.sha256',
        return_value=Mock(
            digest=Mock(return_value=code_challenge_digest),
        ),
    )

    service = OktaService()

    # act
    result = service.get_auth_uri()

    # assert
    set_cache_mock.assert_called_once_with(
        value=code_verifier_encoded,
        key=state,
    )
    expected_base = f'https://{domain}/oauth2/default/v1/authorize'
    assert result.startswith(expected_base)
    assert f'client_id={client_id}' in result
    assert f'state={state}' in result
    encrypt_mock.assert_called_once_with(domain)


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
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'
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
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'
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
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'
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
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.OKTA_CLIENT_ID = client_id
    settings_mock.OKTA_CLIENT_SECRET = client_secret
    settings_mock.OKTA_REDIRECT_URI = redirect_uri
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
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
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'
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
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.OKTA_CLIENT_ID = client_id
    settings_mock.OKTA_CLIENT_SECRET = client_secret
    settings_mock.OKTA_REDIRECT_URI = redirect_uri
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
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
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
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
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.OKTA_DOMAIN = domain
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
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


def test_get_config__domain_not_found_fallback_to_default__ok(mocker):
    """If domain configuration is not found, default configuration is used."""
    # arrange
    domain = 'nonexistent.domain.com'
    default_client_id = 'default_client_id'
    default_client_secret = 'default_client_secret'
    default_domain = 'dev-default.okta.com'
    default_redirect_uri = 'https://default.redirect/uri'
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.OKTA_CLIENT_ID = default_client_id
    settings_mock.OKTA_CLIENT_SECRET = default_client_secret
    settings_mock.OKTA_DOMAIN = default_domain
    settings_mock.OKTA_REDIRECT_URI = default_redirect_uri
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }

    # act
    service = OktaService(domain=domain)

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
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.OKTA_CLIENT_SECRET = None
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }

    # act
    with pytest.raises(exceptions.OktaServiceException) as exc_info:
        OktaService(domain=domain)

    # assert
    assert str(exc_info.value) == MSG_AU_0018(domain)


def test_save_tokens_for_user__create__ok(mocker):
    # arrange
    user = create_test_admin()
    access_token = 'test_access_token'
    expires_in = 3600
    tokens_data = {
        'access_token': access_token,
        'expires_in': expires_in,
    }
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'
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


def test_save_tokens_for_user__update__ok(mocker):
    # arrange
    user = create_test_admin()
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
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'
    service = OktaService()
    service.tokens = new_tokens_data

    # act
    service.save_tokens_for_user(user)

    # assert
    old_token.refresh_from_db()
    assert old_token.access_token == new_tokens_data['access_token']
    assert old_token.refresh_token == ''
    assert old_token.expires_in == new_tokens_data['expires_in']


def test_save_tokens_for_user__with_id_token__cache_user_by_sub(mocker):
    # arrange
    user = create_test_admin()
    access_token = 'test_access_token'
    id_token = 'test_id_token'
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    expires_in = 3600
    tokens_data = {
        'access_token': access_token,
        'id_token': id_token,
        'expires_in': expires_in,
    }
    id_payload = {
        'sub': okta_sub,
        'iss': 'https://dev-123456.okta.com/oauth2/default',
        'aud': 'test_client_id',
    }
    jwt_decode_mock = mocker.patch(
        'src.authentication.services.okta.jwt.decode',
        return_value=id_payload,
    )
    cache_user_by_sub_mock = mocker.patch(
        'src.authentication.services.okta.'
        'OktaService._cache_user_by_sub',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'
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
    jwt_decode_mock.assert_called_once_with(
        id_token,
        options={
            "verify_signature": False,
            "verify_exp": False,
            "verify_aud": False,
            "verify_iss": False,
        },
    )
    cache_user_by_sub_mock.assert_called_once_with(okta_sub, user)


def test_save_tokens_for_user__no_id_token__no_caching(mocker):
    # arrange
    user = create_test_admin()
    access_token = 'test_access_token'
    expires_in = 3600
    tokens_data = {
        'access_token': access_token,
        'expires_in': expires_in,
    }
    jwt_decode_mock = mocker.patch(
        'src.authentication.services.okta.jwt.decode',
    )
    cache_user_by_sub_mock = mocker.patch(
        'src.authentication.services.okta.'
        'OktaService._cache_user_by_sub',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'
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
    jwt_decode_mock.assert_not_called()
    cache_user_by_sub_mock.assert_not_called()


def test_save_tokens_for_user__invalid_id_token__no_caching(mocker):
    # arrange
    user = create_test_admin()
    access_token = 'test_access_token'
    id_token = 'invalid_id_token'
    expires_in = 3600
    tokens_data = {
        'access_token': access_token,
        'id_token': id_token,
        'expires_in': expires_in,
    }
    jwt_decode_mock = mocker.patch(
        'src.authentication.services.okta.jwt.decode',
        side_effect=DecodeError('Invalid token'),
    )
    cache_user_by_sub_mock = mocker.patch(
        'src.authentication.services.okta.'
        'OktaService._cache_user_by_sub',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'
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
    jwt_decode_mock.assert_called_once()
    cache_user_by_sub_mock.assert_not_called()


def test_save_tokens_for_user__invalid_token_error__no_caching(mocker):
    # arrange
    user = create_test_admin()
    access_token = 'test_access_token'
    id_token = 'invalid_id_token'
    expires_in = 3600
    tokens_data = {
        'access_token': access_token,
        'id_token': id_token,
        'expires_in': expires_in,
    }
    jwt_decode_mock = mocker.patch(
        'src.authentication.services.okta.jwt.decode',
        side_effect=InvalidTokenError('Invalid token'),
    )
    cache_user_by_sub_mock = mocker.patch(
        'src.authentication.services.okta.'
        'OktaService._cache_user_by_sub',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'
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
    jwt_decode_mock.assert_called_once()
    cache_user_by_sub_mock.assert_not_called()


def test_save_tokens_for_user__no_sub_in_id_token__no_caching(mocker):
    # arrange
    user = create_test_admin()
    access_token = 'test_access_token'
    id_token = 'test_id_token'
    expires_in = 3600
    tokens_data = {
        'access_token': access_token,
        'id_token': id_token,
        'expires_in': expires_in,
    }
    id_payload = {
        'iss': 'https://dev-123456.okta.com/oauth2/default',
        'aud': 'test_client_id',
    }
    jwt_decode_mock = mocker.patch(
        'src.authentication.services.okta.jwt.decode',
        return_value=id_payload,
    )
    cache_user_by_sub_mock = mocker.patch(
        'src.authentication.services.okta.'
        'OktaService._cache_user_by_sub',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'
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
    jwt_decode_mock.assert_called_once()
    cache_user_by_sub_mock.assert_not_called()


def test_cache_user_by_sub__ok(mocker):
    # arrange
    user = create_test_admin()
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    cache_mock = Mock()
    mocker.patch(
        'src.authentication.services.okta.caches',
        {'default': cache_mock},
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'
    service = OktaService()

    # act
    service._cache_user_by_sub(okta_sub, user)

    # assert
    cache_mock.set.assert_called_once_with(
        f'okta_sub_to_user_{okta_sub}',
        user.id,
        timeout=2592000,
    )


def test_authenticate_user__existing_user__ok(mocker):
    # arrange
    user = create_test_admin(email='test@example.com')
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
    user_filter_mock = mocker.patch(
        'src.authentication.services.base_sso.UserModel.objects.filter',
    )
    user_filter_mock.return_value.first.return_value = user
    save_tokens_mock = mocker.patch(
        'src.authentication.services.okta.OktaService.save_tokens_for_user',
    )
    analytics_mock = mocker.patch(
        'src.authentication.services.base_sso.AnalyticService.users_logged_in',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
    }
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'

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
    user_filter_mock.assert_called_once_with(email='test@example.com')
    user_filter_mock.return_value.first.assert_called_once()
    get_auth_token_mock.assert_called_once_with(
        user=user,
        user_agent=user_agent,
        user_ip=user_ip,
    )
    save_tokens_mock.assert_called_once_with(user)
    analytics_mock.assert_called_once()


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
    access_token = 'okta_access_token'
    code = 'test_code'
    state = 'test_state'
    user_agent = 'Test-Agent'
    user_ip = '127.0.0.1'
    user_profile = {
        'sub': '00uid4BxXw6I6TV4m0g3',
        'email': 'invited@example.com',
        'given_name': 'Updated',
        'family_name': 'Name',
    }
    user_data = {
        'email': 'invited@example.com',
        'first_name': 'Updated',
        'last_name': 'Name',
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
        return_value=user_data,
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService.get_auth_token',
        return_value=token,
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.okta.OktaService.save_tokens_for_user',
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
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
        'BILLING': False,
    }
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'
    service = OktaService()

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


def test_authenticate_user__inactive_user_creates_new__ok(mocker):
    """Inactive user is treated as non-existent and new user is created."""
    # arrange
    account = create_test_account()
    inactive_user = create_test_admin(
        email='inactive@example.com',
        account=account,
        status=UserStatus.INACTIVE,
    )
    new_user = create_test_admin(
        email='inactive@example.com',
        account=account,
    )
    token = 'test_token'
    access_token = 'okta_access_token'
    code = 'test_code'
    state = 'test_state'
    user_agent = 'Test-Agent'
    user_ip = '127.0.0.1'
    user_profile = {
        'sub': '00uid4BxXw6I6TV4m0g3',
        'email': 'inactive@example.com',
        'given_name': 'New',
        'family_name': 'User',
    }
    user_data = {
        'email': 'inactive@example.com',
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
        return_value=user_data,
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService.get_auth_token',
        return_value=token,
    )
    save_tokens_mock = mocker.patch(
        'src.authentication.services.okta.OktaService.save_tokens_for_user',
    )
    user_filter_mock = mocker.patch(
        'src.authentication.services.base_sso.UserModel.objects.filter',
    )
    user_filter_mock.return_value.first.return_value = inactive_user
    join_existing_account_mock = mocker.patch(
        'src.authentication.services.base_sso.BaseSSOService'
        '.join_existing_account',
        return_value=new_user,
    )
    update_users_counts_mock = mocker.patch(
        'src.accounts.services.account.AccountService.update_users_counts',
    )
    users_logged_in_mock = mocker.patch(
        'src.analysis.services.AnalyticService.users_logged_in',
    )
    account_first_mock = mocker.patch.object(
        Account.objects,
        'first',
        return_value=account,
    )
    settings_mock = mocker.patch(
        'src.authentication.services.base_sso.settings',
    )
    mocker.patch(
        'src.authentication.services.okta.settings',
        new=settings_mock,
    )
    settings_mock.PROJECT_CONF = {
        'SSO_AUTH': True,
        'SSO_PROVIDER': 'okta',
        'BILLING': False,
    }
    settings_mock.OKTA_CLIENT_SECRET = 'test_secret'
    service = OktaService()

    # act
    result_user, result_token = service.authenticate_user(
        code,
        state,
        user_agent,
        user_ip,
    )

    # assert
    assert result_user == new_user
    assert result_token == token
    get_first_access_token_mock.assert_called_once_with(code, state)
    get_user_profile_mock.assert_called_once_with(access_token)
    get_user_data_mock.assert_called_once_with(user_profile)
    user_filter_mock.assert_called_once_with(email='inactive@example.com')
    account_first_mock.assert_called_once()
    join_existing_account_mock.assert_called_once_with(
        account=account,
        **user_data,
    )
    update_users_counts_mock.assert_called_once()
    get_auth_token_mock.assert_called_once_with(
        user=new_user,
        user_agent=user_agent,
        user_ip=user_ip,
    )
    save_tokens_mock.assert_called_once_with(new_user)
    users_logged_in_mock.assert_called_once()
