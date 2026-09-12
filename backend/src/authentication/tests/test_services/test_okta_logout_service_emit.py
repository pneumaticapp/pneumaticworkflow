import pytest
from django.core.exceptions import ObjectDoesNotExist

from src.accounts.enums import SourceType
from src.authentication.services.okta_logout import OktaLogoutService
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
    LogoutReason,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
)

pytestmark = pytest.mark.django_db


def test_logout_user__user_found__emit_system_logout(
    mocker,
    fake_stream,
):

    """ Okta ended the sessions, not the person: the actor is the
        system. """

    # arrange
    account = create_test_account()
    user = create_test_admin(account=account)
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    caches_mock = mocker.patch(
        'src.authentication.services.okta_logout.caches',
        new={'default': mocker.Mock()},
    )
    expire_all_tokens_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'PneumaticToken.expire_all_tokens',
    )
    service = OktaLogoutService()

    # act
    service._logout_user(
        user=user,
        sub=okta_sub,
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_LOGOUT
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(type=ActorType.SYSTEM)
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {
        'source': SourceType.OKTA,
        'reason': LogoutReason.IDENTITY_PROVIDER,
    }
    assert event.pii == ()
    caches_mock['default'].delete.assert_called_once_with(
        f'okta_sub_to_user_{okta_sub}',
    )
    expire_all_tokens_mock.assert_called_once_with(user)


def test_logout_user__expire_tokens_failed__no_event(
    mocker,
    fake_stream,
):

    # arrange
    user = create_test_admin()
    okta_sub = '00uid4BxXw6I6TV4m0g3'
    caches_mock = mocker.patch(
        'src.authentication.services.okta_logout.caches',
        new={'default': mocker.Mock()},
    )
    expire_all_tokens_mock = mocker.patch(
        'src.authentication.services.okta_logout.'
        'PneumaticToken.expire_all_tokens',
        side_effect=ValueError('broken'),
    )
    service = OktaLogoutService()

    # act
    with pytest.raises(ValueError) as ex:
        service._logout_user(
            user=user,
            sub=okta_sub,
        )

    # assert
    assert str(ex.value) == 'broken'
    assert fake_stream.events == []
    caches_mock['default'].delete.assert_called_once_with(
        f'okta_sub_to_user_{okta_sub}',
    )
    expire_all_tokens_mock.assert_called_once_with(user)


def test_process_logout__user_not_found__no_event(
    mocker,
    fake_stream,
):

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
    assert fake_stream.events == []
    get_valid_user_sub_mock.assert_called_once_with('test_token')
    get_user_by_cached_sub_mock.assert_called_once_with(okta_sub)
