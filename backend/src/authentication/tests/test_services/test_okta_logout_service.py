import pytest
from unittest.mock import Mock
from django.contrib.auth import get_user_model

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
    get_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_user_by_sub',
        return_value=user,
    )
    logout_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._logout_user',
    )
    validate_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._validate_logout_token',
    )
    service = OktaLogoutService(logout_token='test_token')

    request_data = {
        'format': 'iss_sub',
        'iss': 'https://dev-123456.okta.com/oauth2/default',
        'sub': okta_sub,
    }

    # act
    service.process_logout(**request_data)

    # assert
    validate_mock.assert_called_once()
    get_user_mock.assert_called_once_with(okta_sub)
    logout_user_mock.assert_called_once_with(user, okta_sub=okta_sub)


def test_process_logout__user_not_found__raise_exception(mocker):
    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    get_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_user_by_sub',
        side_effect=user_model.DoesNotExist('User not found'),
    )
    logout_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._logout_user',
    )
    capture_sentry_mock = mocker.patch(
        'src.authentication.services.okta_logout.capture_sentry_message',
    )
    service = OktaLogoutService()

    request_data = {
        'format': 'iss_sub',
        'iss': 'https://dev-123456.okta.com/oauth2/default',
        'sub': okta_sub,
    }

    # act & assert
    with pytest.raises(user_model.DoesNotExist):
        service.process_logout(**request_data)

    get_user_mock.assert_called_once_with(okta_sub)
    logout_user_mock.assert_not_called()
    capture_sentry_mock.assert_called_once()


def test_get_user_by_sub__user_found__return_user(mocker):
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
    result = service._get_user_by_sub(okta_sub)

    # assert
    assert result == user
    cache_mock.get.assert_called_once_with(f'okta_sub_to_user_{okta_sub}')


def test_get_user_by_sub__user_not_cached__raise_exception(mocker):
    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    cache_mock = Mock()
    cache_mock.get.return_value = None
    mocker.patch(
        'src.authentication.services.okta_logout.caches',
        {'default': cache_mock},
    )
    service = OktaLogoutService()

    # act & assert
    with pytest.raises(user_model.DoesNotExist):
        service._get_user_by_sub(okta_sub)

    cache_mock.get.assert_called_once_with(f'okta_sub_to_user_{okta_sub}')


def test_get_user_by_sub__user_not_exist__clear_cache_raise_exception(
    mocker,
):
    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    non_existent_user_id = 99999
    cache_mock = Mock()
    cache_mock.get.return_value = non_existent_user_id
    mocker.patch(
        'src.authentication.services.okta_logout.caches',
        {'default': cache_mock},
    )
    service = OktaLogoutService()

    # act & assert
    with pytest.raises(user_model.DoesNotExist):
        service._get_user_by_sub(okta_sub)

    cache_mock.get.assert_called_once_with(f'okta_sub_to_user_{okta_sub}')
    cache_mock.delete.assert_called_once_with(
        f'okta_sub_to_user_{okta_sub}',
    )


def test_logout_user__with_access_token__cleanup_all(mocker):
    # arrange
    user = create_test_admin()
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    access_token_1 = 'access_token_1'

    # Create access token (only one per user-source combination allowed)
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
    service._logout_user(user, okta_sub=okta_sub)

    # assert
    assert AccessToken.objects.filter(
        user=user,
        source=SourceType.OKTA,
    ).count() == 0
    # Check profile cache deletion
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
    service._logout_user(user, okta_sub=okta_sub)

    # assert
    # Only sub cache should be cleared, no profile cache
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
    service._logout_user(user, okta_sub=None)

    # assert
    # No sub cache should be cleared
    cache_mock.delete.assert_not_called()
    expire_tokens_mock.assert_called_once_with(user)
