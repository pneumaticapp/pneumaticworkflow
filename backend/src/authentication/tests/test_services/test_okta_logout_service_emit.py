import pytest
from django.core.exceptions import ObjectDoesNotExist

from src.accounts.enums import SourceType
from src.authentication.services.okta_logout import OktaLogoutService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
)

pytestmark = pytest.mark.django_db


def test_logout_user__user_found__audit_logged_out_by_provider(mocker):

    # arrange
    account = create_test_account()
    user = create_test_admin(account=account)
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    expire_all_tokens_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'PneumaticToken.expire_all_tokens',
    )
    user_logged_out_by_provider_mock = mocker.patch(
        'src.authentication.services.okta_logout.AuditEventService.'
        'user_logged_out_by_provider',
    )
    service = OktaLogoutService()
    cache_delete_mock = mocker.patch.object(
        service.cache,
        attribute='delete',
    )

    # act
    service._logout_user(
        user=user,
        sub=okta_sub,
    )

    # assert
    user_logged_out_by_provider_mock.assert_called_once_with(
        target=user,
        source=SourceType.OKTA,
    )
    cache_delete_mock.assert_called_once_with(
        f'okta_sub_to_user_{okta_sub}',
    )
    expire_all_tokens_mock.assert_called_once_with(user)


def test_logout_user__expire_tokens_failed__audit_not_called(mocker):

    # arrange
    user = create_test_admin()
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    expire_all_tokens_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'PneumaticToken.expire_all_tokens',
        side_effect=ValueError('broken'),
    )
    user_logged_out_by_provider_mock = mocker.patch(
        'src.authentication.services.okta_logout.AuditEventService.'
        'user_logged_out_by_provider',
    )
    service = OktaLogoutService()
    cache_delete_mock = mocker.patch.object(
        service.cache,
        attribute='delete',
    )

    # act
    with pytest.raises(ValueError) as ex:
        service._logout_user(
            user=user,
            sub=okta_sub,
        )

    # assert
    assert str(ex.value) == 'broken'
    user_logged_out_by_provider_mock.assert_not_called()
    cache_delete_mock.assert_called_once_with(
        f'okta_sub_to_user_{okta_sub}',
    )
    expire_all_tokens_mock.assert_called_once_with(user)


def test_process_logout__user_not_found__audit_not_called(mocker):

    # arrange
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    get_valid_user_sub_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_valid_user_sub',
        return_value=okta_sub,
    )
    get_user_by_cached_sub_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'OktaLogoutService._get_user_by_cached_sub',
        side_effect=ObjectDoesNotExist('User not found'),
    )
    user_logged_out_by_provider_mock = mocker.patch(
        'src.authentication.services.okta_logout.AuditEventService.'
        'user_logged_out_by_provider',
    )
    service = OktaLogoutService()

    # act
    with pytest.raises(ObjectDoesNotExist) as ex:
        service.process_logout(
            token='test_token',
            logout_format='iss_sub',
            data={
                'format': 'iss_sub',
                'iss': 'https://dev-123456.okta.com/oauth2/default',
                'sub': okta_sub,
            },
        )

    # assert
    assert str(ex.value) == 'User not found'
    user_logged_out_by_provider_mock.assert_not_called()
    get_valid_user_sub_mock.assert_called_once_with('test_token')
    get_user_by_cached_sub_mock.assert_called_once_with(okta_sub)
