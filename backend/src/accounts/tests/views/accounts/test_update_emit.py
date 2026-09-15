import pytest

from src.accounts.enums import UserType
from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    AccountEvents,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_partial_update__name_changed__emit_changed_field_names(
    api_client,
    group_mock,
    fake_stream,
):

    # arrange
    account = create_test_account(name='Old name')
    owner = create_test_owner(account=account)
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.8',
    )

    # act
    response = api_client.put(
        '/accounts/account',
        data={'name': 'New name', 'logo_lg': None},
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == AccountEvents.UPDATE
    assert event.category == AccountEvents.CATEGORY
    assert event.account_id == account.id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventObjectType.ACCOUNT,
        id=account.id,
    )
    assert event.payload == {'changed_fields': ['name']}
    assert event.ip == '10.10.0.8'
    group_mock.assert_called_once_with(user=owner, account=account)


def test_partial_update__same_values__no_event(
    api_client,
    group_mock,
    fake_stream,
):

    """ The form sends every field on every save: an update that
        changes nothing is not an action worth a record. """

    # arrange
    account = create_test_account(name='Same name')
    owner = create_test_owner(account=account)
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        '/accounts/account',
        data={'name': 'Same name'},
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert fake_stream.events == []
    group_mock.assert_called_once_with(user=owner, account=account)


def test_partial_update__not_admin__no_event(
    api_client,
    group_mock,
    fake_stream,
):

    # arrange
    account = create_test_account(name='Old name')
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/account',
        data={'name': 'New name'},
        format='json',
    )

    # assert
    assert response.status_code == 403
    assert fake_stream.events == []
    group_mock.assert_not_called()
