import pytest
import jwt
import requests
from unittest.mock import Mock
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from src.accounts.enums import SourceType
from src.authentication.models import AccessToken
from src.authentication.services.okta_logout import OktaLogoutService
from src.processes.tests.fixtures import create_test_admin

pytestmark = pytest.mark.django_db
user_model = get_user_model()


def test_process_logout__user_found__ok(mocker):
    # arrange
    user = create_test_admin()
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    logout_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._logout_user',
    )
    get_valid_sub_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_valid_user_sub',
        return_value=okta_sub,
    )
    get_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_user_by_cached_sub',
        return_value=user,
    )
    service = OktaLogoutService()

    data = {
        'format': 'iss_sub',
        'iss': 'https://dev-123456.okta.com/oauth2/default',
        'sub': okta_sub,
    }

    # act
    service.process_logout(
        token='test_token',
        logout_format='iss_sub',
        data=data,
    )

    # assert
    get_valid_sub_mock.assert_called_once_with('test_token')
    get_user_mock.assert_called_once_with(okta_sub)
    logout_user_mock.assert_called_once_with(user=user, sub=okta_sub)


def test_process_logout__user_not_found__no_logout(mocker):
    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    logout_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._logout_user',
    )
    get_valid_sub_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_valid_user_sub',
        return_value=okta_sub,
    )
    get_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_user_by_cached_sub',
        side_effect=ObjectDoesNotExist('User not found'),
    )
    service = OktaLogoutService()

    data = {
        'format': 'iss_sub',
        'iss': 'https://dev-123456.okta.com/oauth2/default',
        'sub': okta_sub,
    }

    # act
    with pytest.raises(ObjectDoesNotExist):
        service.process_logout(
            token='test_token',
            logout_format='iss_sub',
            data=data,
        )

    # assert
    get_valid_sub_mock.assert_called_once_with('test_token')
    get_user_mock.assert_called_once_with(okta_sub)
    logout_user_mock.assert_not_called()


def test_get_user_by_cached_sub__user_found__return_user(mocker):
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
    result = service._get_user_by_cached_sub(okta_sub)

    # assert
    assert result == user
    cache_mock.get.assert_called_once_with(f'okta_sub_to_user_{okta_sub}')


def test_get_user_by_cached_sub__user_not_cached__return_none(mocker):
    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    cache_mock = Mock()
    cache_mock.get.return_value = None
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    mocker.patch(
        'src.authentication.services.okta_logout.caches',
        {'default': cache_mock},
    )
    service = OktaLogoutService()

    # act
    with pytest.raises(ObjectDoesNotExist):
        service._get_user_by_cached_sub(okta_sub)

    # assert
    cache_mock.get.assert_called_once_with(f'okta_sub_to_user_{okta_sub}')
    capture_sentry_mock.assert_called_once()


def test_get_user_by_cached_sub__user_not_exist__clear_cache_return_none(
    mocker,
):
    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    non_existent_user_id = 99999
    cache_mock = Mock()
    cache_mock.get.return_value = non_existent_user_id
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    mocker.patch(
        'src.authentication.services.okta_logout.caches',
        {'default': cache_mock},
    )
    service = OktaLogoutService()

    # act
    with pytest.raises(ObjectDoesNotExist):
        service._get_user_by_cached_sub(okta_sub)

    # assert
    cache_mock.get.assert_called_once_with(f'okta_sub_to_user_{okta_sub}')
    cache_mock.delete.assert_called_once_with(
        f'okta_sub_to_user_{okta_sub}',
    )
    capture_sentry_mock.assert_called_once()
    assert f'Cached user not found: {non_existent_user_id}' in (
        capture_sentry_mock.call_args[1]['message']
    )


def test_process_logout_with_jwt_token__ok(mocker):
    # arrange
    user = create_test_admin()
    jwt_sub = '0oaz5d6sikQdT7FMX697'
    request_sub = '00uz5dexshp1ALzYF697'

    get_valid_sub_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_valid_user_sub',
        return_value=jwt_sub,
    )

    get_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_user_by_cached_sub',
        return_value=user,
    )

    logout_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._logout_user',
    )

    service = OktaLogoutService()

    data = {
        'format': 'iss_sub',
        'iss': 'https://trial-4235207.okta.com',
        'sub': request_sub,
    }

    # act
    service.process_logout(
        token='test_token',
        logout_format='iss_sub',
        data=data,
    )

    # assert
    get_valid_sub_mock.assert_called_once_with('test_token')
    get_user_mock.assert_called_once_with(request_sub)
    logout_user_mock.assert_called_once_with(user=user, sub=jwt_sub)


def test_logout_user__with_access_token__cleanup_all(mocker):
    # arrange
    user = create_test_admin()
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    access_token_1 = 'access_token_1'

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
    service._logout_user(user, okta_sub)

    # assert
    assert AccessToken.objects.filter(
        user=user,
        source=SourceType.OKTA,
    ).count() == 0
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
    service._logout_user(user, okta_sub)

    # assert
    cache_mock.delete.assert_called_once_with(
        f'okta_sub_to_user_{okta_sub}',
    )
    expire_tokens_mock.assert_called_once_with(user)


def test_get_valid_user_sub__valid_token__ok(mocker):
    # arrange
    logout_token = 'test_logout_token'
    domain = 'dev-123456.okta.com'
    expected_sub = 'test_sub'
    expected_payload = {'sub': expected_sub, 'aud': 'test_client_id'}

    mocker.patch(
        'src.authentication.services.okta_logout.jwt.get_unverified_header',
        return_value={'kid': 'test_kid'},
    )
    mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_public_key_pem',
        return_value='test_pem_key',
    )
    mocker.patch(
        'src.authentication.services.okta_logout.jwt.decode',
        return_value=expected_payload,
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta_logout.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    service = OktaLogoutService()

    # act
    result = service._get_valid_user_sub(logout_token)

    # assert
    assert result == expected_sub


def test_get_valid_user_sub__no_kid__raise_value_error(mocker):
    # arrange
    logout_token = 'test_logout_token'
    domain = 'dev-123456.okta.com'

    mocker.patch(
        'src.authentication.services.okta_logout.jwt.get_unverified_header',
        return_value={'kid': 'test_kid'},
    )
    mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_public_key_pem',
        return_value='test_pem_key',
    )
    mocker.patch(
        'src.authentication.services.okta_logout.jwt.decode',
        side_effect=jwt.DecodeError('Invalid token'),
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta_logout.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    service = OktaLogoutService()

    # act
    with pytest.raises(jwt.DecodeError):
        service._get_valid_user_sub(logout_token)

    # assert
    capture_sentry_mock.assert_called_once()
    assert 'JWT token validation failed' in (
        capture_sentry_mock.call_args[1]['message']
    )


def test_get_valid_user_sub__jwt_decode_error__raise_exception(mocker):
    # arrange
    logout_token = 'test_logout_token'
    domain = 'dev-123456.okta.com'

    mocker.patch(
        'src.authentication.services.okta_logout.jwt.get_unverified_header',
        return_value={'kid': 'test_kid'},
    )
    mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_public_key_pem',
        return_value='test_pem_key',
    )
    mocker.patch(
        'src.authentication.services.okta_logout.jwt.decode',
        side_effect=jwt.DecodeError('Invalid token'),
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta_logout.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    service = OktaLogoutService()

    # act
    with pytest.raises(jwt.DecodeError):
        service._get_valid_user_sub(logout_token)

    # assert
    capture_sentry_mock.assert_called_once()
    assert 'JWT token validation failed' in (
        capture_sentry_mock.call_args[1]['message']
    )


def test_get_public_key_pem__key_found__return_pem(mocker):
    # arrange
    kid = 'test_kid'
    jwks = {
        'keys': [
            {
                'kid': kid,
                'n': 'test_n',
                'e': 'AQAB',
            },
        ],
    }
    mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_jwks',
        return_value=jwks,
    )
    mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_jwk_as_pem',
        return_value='test_pem',
    )
    service = OktaLogoutService()

    # act
    result = service._get_public_key_pem(kid)

    # assert
    assert result == 'test_pem'


def test_get_public_key_pem__key_not_found__raise_value_error(mocker):
    # arrange
    kid = 'test_kid'
    jwks = {
        'keys': [
            {
                'kid': 'other_kid',
                'n': 'test_n',
                'e': 'AQAB',
            },
        ],
    }
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_jwks',
        return_value=jwks,
    )
    service = OktaLogoutService()

    # act
    with pytest.raises(ValueError, match=f'Key with kid={kid} not found'):
        service._get_public_key_pem(kid)

    # assert
    capture_sentry_mock.assert_called_once()
    assert f"Key with kid={kid} not found" in (
        capture_sentry_mock.call_args[1]['message']
    )


def test_get_jwks__success__return_jwks(mocker):
    # arrange
    jwks_data = {'keys': []}
    response_mock = Mock()
    response_mock.json.return_value = jwks_data
    response_mock.raise_for_status = Mock()
    request_mock = mocker.patch(
        'src.authentication.services.okta_logout.requests.get',
        return_value=response_mock,
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta_logout.settings',
    )
    settings_mock.OKTA_DOMAIN = 'dev-123456.okta.com'
    service = OktaLogoutService()

    # act
    result = service._get_jwks()

    # assert
    assert result == jwks_data
    request_mock.assert_called_once()


def test_get_jwks__request_exception__raise_exception(mocker):
    # arrange
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    mocker.patch(
        'src.authentication.services.okta_logout.requests.get',
        side_effect=requests.RequestException('Connection error'),
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta_logout.settings',
    )
    settings_mock.OKTA_DOMAIN = 'dev-123456.okta.com'
    service = OktaLogoutService()

    # act
    with pytest.raises(requests.RequestException):
        service._get_jwks()

    # assert
    capture_sentry_mock.assert_called_once()
    assert "Failed to fetch JWKS: " in (
        capture_sentry_mock.call_args[1]['message']
    )
