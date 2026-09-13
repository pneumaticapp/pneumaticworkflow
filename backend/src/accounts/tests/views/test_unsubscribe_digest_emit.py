import pytest

from src.accounts.tokens import DigestUnsubscribeToken
from src.accounts.views.unsubscribes import DIGEST_SUBSCRIPTION_FIELD
from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_unsubscribe__valid_token__emit_actor_is_token_user(
    mocker,
    api_client,
    fake_stream,
):

    """ The link carries no authentication: the person it was sent to
        is the actor. """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    token = str(DigestUnsubscribeToken.for_user(user))
    users_digest_mock = mocker.patch(
        'src.accounts.views.unsubscribes.AnalyticService.users_digest',
    )

    # act
    response = api_client.get(f'/accounts/digest/unsubscribe?token={token}')

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_digest_subscriber is False
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_UNSUBSCRIBE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=user.id,
        email=user.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {'email_type': DIGEST_SUBSCRIPTION_FIELD}
    users_digest_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_unsubscribe__incorrect_token__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    user = create_test_owner()
    users_digest_mock = mocker.patch(
        'src.accounts.views.unsubscribes.AnalyticService.users_digest',
    )

    # act
    response = api_client.get('/accounts/digest/unsubscribe?token=12345')

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_digest_subscriber is True
    assert fake_stream.events == []
    users_digest_mock.assert_not_called()


def test_unsubscribe__no_token__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    user = create_test_owner()
    users_digest_mock = mocker.patch(
        'src.accounts.views.unsubscribes.AnalyticService.users_digest',
    )

    # act
    response = api_client.get('/accounts/digest/unsubscribe')

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_digest_subscriber is True
    assert fake_stream.events == []
    users_digest_mock.assert_not_called()
