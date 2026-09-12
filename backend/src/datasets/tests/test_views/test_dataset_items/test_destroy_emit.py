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
    create_test_dataset,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_destroy__owner__emit_dataset_item_delete(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=1)
    item = dataset.items.get()
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.delete(path=f'/datasets/items/{item.id}')

    # assert
    assert response.status_code == 204
    assert dataset.items.count() == 0
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.DATASET_ITEM_DELETE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.DATASET_ITEM,
        id=item.id,
    )
    assert event.payload == {'dataset_id': dataset.id}


def test_destroy__another_account__no_event(
    api_client,
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    another_account = create_test_account(name='Another Company')
    dataset = create_test_dataset(account=another_account, items_count=1)
    item = dataset.items.get()
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.delete(path=f'/datasets/items/{item.id}')

    # assert
    assert response.status_code == 404
    assert dataset.items.count() == 1
    assert fake_stream.events == []
