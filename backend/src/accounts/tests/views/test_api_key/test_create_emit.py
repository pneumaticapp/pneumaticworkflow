import pytest

from src.accounts.services.api_key import APIKeyService
from src.logs.events.enums import (
    ActorType,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject, to_json
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_create__api_keys_endpoint__event_has_no_raw_key(
    api_client,
    fake_stream,
):

    """ The whole record written to the stream is checked, not the
        payload alone: a key that reaches a log backend is a key an
        operator of that backend can sign in with. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.12',
    )

    # act
    response = api_client.post(
        path='/accounts/api-keys',
        data={'name': 'CI key'},
        HTTP_X_REQUEST_ID='audit-api-key-1',
    )

    # assert
    assert response.status_code == 201
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    record = to_json(event.to_dict())
    assert response.data['token'] not in record
    assert 'token' not in event.payload
    assert event.type == EventName.API_KEY_CREATE
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.API_KEY,
        id=response.data['id'],
    )
    assert event.payload == {
        'name': 'CI key',
        'target_user_id': owner.id,
    }
    assert event.ip == '10.10.0.12'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-api-key-1'


def test_create__not_admin__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    create_mock = mocker.patch.object(APIKeyService, attribute='create')
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/accounts/api-keys',
        data={'name': 'CI key'},
    )

    # assert
    assert response.status_code == 403
    assert fake_stream.events == []
    create_mock.assert_not_called()
