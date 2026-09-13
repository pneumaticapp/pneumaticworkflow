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
    create_test_api_key,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_destroy__api_keys_endpoint__event_has_no_raw_key(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_key = create_test_api_key(user=owner, name='To revoke')
    api_client.token_authenticate(owner)

    # act
    response = api_client.delete(f'/accounts/api-keys/{api_key.id}')

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    record = to_json(event.to_dict())
    assert api_key.token not in record
    assert event.type == EventName.API_KEY_REVOKE
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.API_KEY,
        id=api_key.id,
    )
    assert event.payload == {
        'name': 'To revoke',
        'target_user_id': owner.id,
    }


def test_destroy__key_of_another_account__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    other_account = create_test_account(name='Other')
    other_owner = create_test_owner(
        account=other_account,
        email='other@test.test',
    )
    api_key = create_test_api_key(user=other_owner, name='Other key')
    revoke_mock = mocker.patch.object(APIKeyService, attribute='revoke')
    api_client.token_authenticate(owner)

    # act
    response = api_client.delete(f'/accounts/api-keys/{api_key.id}')

    # assert
    assert response.status_code == 404
    assert fake_stream.events == []
    revoke_mock.assert_not_called()
