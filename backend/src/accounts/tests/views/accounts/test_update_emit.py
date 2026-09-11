import pytest

from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import (
    create_test_account,
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
    assert event.type == EventName.ACCOUNT_UPDATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
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
