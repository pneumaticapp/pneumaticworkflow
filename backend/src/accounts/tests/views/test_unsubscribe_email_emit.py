import pytest

from src.accounts.tokens import UnsubscribeEmailToken
from src.analysis.enums import MailoutType
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


def test_unsubscribe__valid_token__emit_token_email_type(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    token = str(
        UnsubscribeEmailToken.create_token(
            user_id=user.id,
            email_type=MailoutType.TASKS_DIGEST,
        ),
    )

    # act
    response = api_client.get(f'/accounts/emails/unsubscribe?token={token}')

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_tasks_digest_subscriber is False
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
    assert event.payload == {
        'email_type': MailoutType.MAP[MailoutType.TASKS_DIGEST],
    }


def test_unsubscribe__incorrect_token__no_event(
    api_client,
    fake_stream,
):

    # arrange
    user = create_test_owner()

    # act
    response = api_client.get('/accounts/emails/unsubscribe?token=12345')

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_tasks_digest_subscriber is True
    assert fake_stream.events == []


def test_unsubscribe__no_token__no_event(
    api_client,
    fake_stream,
):

    # arrange
    user = create_test_owner()

    # act
    response = api_client.get('/accounts/emails/unsubscribe')

    # assert
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_tasks_digest_subscriber is True
    assert fake_stream.events == []
