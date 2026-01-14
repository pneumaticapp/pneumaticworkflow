import pytest
import jwt
import requests
from unittest.mock import Mock
from django.contrib.auth import get_user_model

from src.accounts.enums import (
    SourceType,
    UserStatus,
)
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
    validate_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
        return_value={'sub': okta_sub},
    )
    get_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_user_by_cached_sub',
        return_value=user,
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
    logout_user_mock.assert_called_once_with(user, okta_sub)


def test_process_logout__user_not_found__no_logout(mocker):
    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    logout_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._logout_user',
    )
    validate_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
        return_value={'sub': okta_sub},
    )
    get_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_user_by_cached_sub',
        return_value=None,
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
    result = service._get_user_by_cached_sub(okta_sub)

    # assert
    assert result is None
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
    result = service._get_user_by_cached_sub(okta_sub)

    # assert
    assert result is None
    cache_mock.get.assert_called_once_with(f'okta_sub_to_user_{okta_sub}')
    cache_mock.delete.assert_called_once_with(
        f'okta_sub_to_user_{okta_sub}',
    )
    capture_sentry_mock.assert_called_once()


def test_process_logout_with_jwt_token__ok(mocker):
    # arrange
    user = create_test_admin()
    jwt_sub = '0oaz5d6sikQdT7FMX697'
    request_sub = '00uz5dexshp1ALzYF697'

    validate_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
        return_value={'sub': jwt_sub},
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

    service = OktaLogoutService(logout_token='test_token')

    sub_id_data = {
        'format': 'iss_sub',
        'iss': 'https://trial-4235207.okta.com',
        'sub': request_sub,
    }
    request_data = {
        'format': 'iss_sub',
        'sub_id_data': sub_id_data,
    }

    # act
    service.process_logout(**request_data)

    # assert
    validate_mock.assert_called_once()
    get_user_mock.assert_called_once_with(request_sub)
    logout_user_mock.assert_called_once_with(user, jwt_sub)


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
    service._logout_user(user, None)

    # assert
    cache_mock.delete.assert_not_called()
    expire_tokens_mock.assert_called_once_with(user)


def test_validate_logout_token__valid_token__ok(mocker):
    # arrange
    logout_token = 'test_logout_token'
    domain = 'dev-123456.okta.com'
    expected_payload = {'sub': 'test_sub', 'aud': 'test_client_id'}

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
    service = OktaLogoutService(logout_token=logout_token)

    # act
    result = service._validate_logout_token()

    # assert
    assert result == expected_payload


def test_validate_logout_token__no_kid__return_none(mocker):
    # arrange
    logout_token = 'test_logout_token'
    domain = 'dev-123456.okta.com'

    mocker.patch(
        'src.authentication.services.okta_logout.jwt.get_unverified_header',
        return_value={},
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta_logout.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    service = OktaLogoutService(logout_token=logout_token)

    # act
    result = service._validate_logout_token()

    # assert
    assert result is None


def test_validate_logout_token__jwt_decode_error__return_none(mocker):
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
    service = OktaLogoutService(logout_token=logout_token)

    # act
    result = service._validate_logout_token()

    # assert
    assert result is None
    capture_sentry_mock.assert_called_once()
    assert 'Okta logout token validation failed' in (
        capture_sentry_mock.call_args[1]['message']
    )


def test_validate_logout_token__request_exception__return_none(mocker):
    # arrange
    logout_token = 'test_logout_token'
    domain = 'dev-123456.okta.com'

    mocker.patch(
        'src.authentication.services.okta_logout.jwt.get_unverified_header',
        side_effect=requests.RequestException('Connection error'),
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta_logout.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    service = OktaLogoutService(logout_token=logout_token)

    # act
    result = service._validate_logout_token()

    # assert
    assert result is None
    capture_sentry_mock.assert_called_once()


def test_validate_logout_token__no_token__return_none(mocker):
    # arrange
    domain = 'dev-123456.okta.com'
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    mocker.patch(
        'src.authentication.services.okta_logout.jwt.get_unverified_header',
        side_effect=TypeError('None type'),
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta_logout.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    service = OktaLogoutService(logout_token=None)

    # act
    result = service._validate_logout_token()

    # assert
    assert result is None
    capture_sentry_mock.assert_called_once()


def test_validate_logout_token__no_public_key__return_none(mocker):
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
        return_value=None,
    )
    settings_mock = mocker.patch(
        'src.authentication.services.okta_logout.settings',
    )
    settings_mock.OKTA_DOMAIN = domain
    service = OktaLogoutService(logout_token=logout_token)

    # act
    result = service._validate_logout_token()

    # assert
    assert result is None


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
        return_value={'sub': 'test_sub'},
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
    logout_user_mock.assert_called_once_with(user, 'test_sub')


def test_process_logout_email_format__user_not_found__log_sentry(mocker):
    # arrange
    email = 'nonexistent@example.com'
    logout_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._logout_user',
    )
    validate_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
        return_value={'sub': 'test_sub'},
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


def test_process_logout_missing_sub_in_iss_sub_format__log_sentry(mocker):
    # arrange
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    validate_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
        return_value={'sub': 'test_sub'},
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
    capture_sentry_mock.assert_called()
    assert 'User identification failed' in (
        capture_sentry_mock.call_args[1]['message']
    )


def test_process_logout_missing_email_in_email_format__log_sentry(mocker):
    # arrange
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    validate_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
        return_value={'sub': 'test_sub'},
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
    capture_sentry_mock.assert_called()
    assert 'User identification failed' in (
        capture_sentry_mock.call_args[1]['message']
    )


def test_process_logout__unsupported_format__log_sentry(mocker):
    # arrange
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    validate_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
        return_value={'sub': 'test_sub'},
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
    capture_sentry_mock.assert_called()
    assert 'User identification failed' in (
        capture_sentry_mock.call_args[1]['message']
    )


def test_process_logout__invalid_token__return_early(mocker):
    # arrange
    validate_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
        return_value=None,
    )
    identify_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._identify_user',
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
    identify_user_mock.assert_not_called()


def test_identify_user__iss_sub_format__user_found(mocker):
    # arrange
    user = create_test_admin()
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    get_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_user_by_cached_sub',
        return_value=user,
    )
    service = OktaLogoutService()

    sub_id_data = {
        'sub': okta_sub,
    }

    # act
    result = service._identify_user('iss_sub', sub_id_data)

    # assert
    assert result == user
    get_user_mock.assert_called_once_with(okta_sub)


def test_identify_user__iss_sub_format__no_sub(mocker):
    # arrange
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    service = OktaLogoutService()

    sub_id_data = {}

    # act
    result = service._identify_user('iss_sub', sub_id_data)

    # assert
    assert result is None
    capture_sentry_mock.assert_called_once()


def test_identify_user__iss_sub_format__user_not_found(mocker):
    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    get_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_user_by_cached_sub',
        return_value=None,
    )
    service = OktaLogoutService()

    sub_id_data = {
        'sub': okta_sub,
    }

    # act
    result = service._identify_user('iss_sub', sub_id_data)

    # assert
    assert result is None
    get_user_mock.assert_called_once_with(okta_sub)


def test_identify_user__email_format__user_found(mocker):
    # arrange
    user = create_test_admin(email='test@example.com')
    service = OktaLogoutService()

    sub_id_data = {
        'email': 'test@example.com',
    }

    # act
    result = service._identify_user('email', sub_id_data)

    # assert
    assert result == user


def test_identify_user__email_format__user_not_found(mocker):
    # arrange
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    service = OktaLogoutService()

    sub_id_data = {
        'email': 'nonexistent@example.com',
    }

    # act
    result = service._identify_user('email', sub_id_data)

    # assert
    assert result is None
    capture_sentry_mock.assert_not_called()


def test_identify_user__email_format__inactive_user(mocker):
    # arrange
    create_test_admin(
        email='inactive@example.com',
        status=UserStatus.INACTIVE,
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    service = OktaLogoutService()

    sub_id_data = {
        'email': 'inactive@example.com',
    }

    # act
    result = service._identify_user('email', sub_id_data)

    # assert
    assert result is None
    capture_sentry_mock.assert_not_called()


def test_identify_user__unsupported_format(mocker):
    # arrange
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    service = OktaLogoutService()

    # act
    result = service._identify_user('unsupported', {})

    # assert
    assert result is None
    capture_sentry_mock.assert_called_once()


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
        'OktaLogoutService._jwk_to_pem',
        return_value='test_pem',
    )
    service = OktaLogoutService()

    # act
    result = service._get_public_key_pem(kid)

    # assert
    assert result == 'test_pem'


def test_get_public_key_pem__key_not_found__return_none(mocker):
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
    result = service._get_public_key_pem(kid)

    # assert
    assert result is None
    capture_sentry_mock.assert_called_once()


def test_get_public_key_pem__no_jwks__return_none(mocker):
    # arrange
    kid = 'test_kid'
    mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_jwks',
        return_value=None,
    )
    service = OktaLogoutService()

    # act
    result = service._get_public_key_pem(kid)

    # assert
    assert result is None


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


def test_get_jwks__request_exception__return_none(mocker):
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
    result = service._get_jwks()

    # assert
    assert result is None
    capture_sentry_mock.assert_called_once()


def test_get_jwks__http_error__return_none(mocker):
    # arrange
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    response_mock = Mock()
    response_mock.raise_for_status.side_effect = (
        requests.HTTPError('404 Not Found')
    )
    mocker.patch(
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
    assert result is None
    capture_sentry_mock.assert_called_once()
