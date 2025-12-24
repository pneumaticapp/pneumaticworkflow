import pytest
from unittest.mock import Mock

from src.accounts.enums import SourceType
from src.authentication.models import AccessToken
from src.authentication.services.okta_logout import OktaLogoutService
from src.processes.tests.fixtures import create_test_admin

pytestmark = pytest.mark.django_db


def test_process_logout__user_found__ok(mocker):
    # arrange
    user = create_test_admin()
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    find_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._find_user_by_okta_sub',
        return_value=user,
    )
    logout_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._logout_user',
    )
    service = OktaLogoutService()

    # act
    service.process_logout(sub=okta_sub)

    # assert
    find_user_mock.assert_called_once_with(okta_sub)
    logout_user_mock.assert_called_once_with(user, okta_sub=okta_sub)


def test_process_logout__user_not_found__no_logout(mocker):
    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    find_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._find_user_by_okta_sub',
        return_value=None,
    )
    logout_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._logout_user',
    )
    service = OktaLogoutService()

    # act
    service.process_logout(sub=okta_sub)

    # assert
    find_user_mock.assert_called_once_with(okta_sub)
    logout_user_mock.assert_not_called()


def test_find_user_by_okta_sub__user_found__return_user(mocker):
    # arrange
    user = create_test_admin()
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    get_cached_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_cached_user_by_sub',
        return_value=user.id,
    )
    service = OktaLogoutService()

    # act
    result = service._find_user_by_okta_sub(okta_sub)

    # assert
    assert result == user
    get_cached_user_mock.assert_called_once_with(okta_sub)


def test_find_user_by_okta_sub__user_not_cached__return_none(mocker):
    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    get_cached_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_cached_user_by_sub',
        return_value=None,
    )
    service = OktaLogoutService()

    # act
    result = service._find_user_by_okta_sub(okta_sub)

    # assert
    assert result is None
    get_cached_user_mock.assert_called_once_with(okta_sub)


def test_find_user_by_okta_sub__user_not_exist__clear_cache_return_none(
    mocker,
):
    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    non_existent_user_id = 99999
    get_cached_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_cached_user_by_sub',
        return_value=non_existent_user_id,
    )
    clear_cached_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._clear_cached_user_by_sub',
    )
    service = OktaLogoutService()

    # act
    result = service._find_user_by_okta_sub(okta_sub)

    # assert
    assert result is None
    get_cached_user_mock.assert_called_once_with(okta_sub)
    clear_cached_user_mock.assert_called_once_with(okta_sub)


def test_get_cached_user_by_sub__ok(mocker):
    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    user_id = 123
    cache_mock = Mock()
    cache_mock.get.return_value = user_id
    mocker.patch(
        'src.authentication.services.okta_logout.caches',
        {'default': cache_mock},
    )
    service = OktaLogoutService()

    # act
    result = service._get_cached_user_by_sub(okta_sub)

    # assert
    assert result == user_id
    cache_mock.get.assert_called_once_with(f'okta_sub_to_user_{okta_sub}')


def test_clear_cached_user_by_sub__ok(mocker):
    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    cache_mock = Mock()
    mocker.patch(
        'src.authentication.services.okta_logout.caches',
        {'default': cache_mock},
    )
    service = OktaLogoutService()

    # act
    service._clear_cached_user_by_sub(okta_sub)

    # assert
    cache_mock.delete.assert_called_once_with(f'okta_sub_to_user_{okta_sub}')


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
    clear_cached_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._clear_cached_user_by_sub',
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
    cache_mock.delete.assert_called_once_with(f'user_profile_{access_token_1}')
    clear_cached_user_mock.assert_called_once_with(okta_sub)
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
    clear_cached_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._clear_cached_user_by_sub',
    )
    expire_tokens_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'PneumaticToken.expire_all_tokens',
    )
    service = OktaLogoutService()

    # act
    service._logout_user(user, okta_sub=okta_sub)

    # assert
    cache_mock.delete.assert_not_called()
    clear_cached_user_mock.assert_called_once_with(okta_sub)
    expire_tokens_mock.assert_called_once_with(user)


def test_logout_user__no_okta_sub__skip_sub_cleanup(mocker):
    # arrange
    user = create_test_admin()

    cache_mock = Mock()
    mocker.patch(
        'src.authentication.services.okta_logout.caches',
        {'default': cache_mock},
    )
    clear_cached_user_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._clear_cached_user_by_sub',
    )
    expire_tokens_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'PneumaticToken.expire_all_tokens',
    )
    service = OktaLogoutService()

    # act
    service._logout_user(user, okta_sub=None)

    # assert
    clear_cached_user_mock.assert_not_called()
    expire_tokens_mock.assert_called_once_with(user)
