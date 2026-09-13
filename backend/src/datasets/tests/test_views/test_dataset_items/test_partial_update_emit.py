import pytest

from src.datasets.exceptions import DataSetServiceException
from src.datasets.messages import MSG_DS_0002
from src.datasets.services.dataset_item import DataSetItemService
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
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_partial_update__value_changed__emit_dataset_item_update(
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
    response = api_client.patch(
        path=f'/datasets/items/{item.id}',
        data={'value': 'Renamed', 'order': item.order},
        format='json',
    )

    # assert
    assert response.status_code == 200
    item.refresh_from_db()
    assert item.value == 'Renamed'
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.DATASET_ITEM_UPDATE
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
    assert event.payload == {
        'dataset_id': dataset.id,
        'changed_fields': ['value'],
    }


def test_partial_update__value_and_order__emit_sorted_fields(
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
    response = api_client.patch(
        path=f'/datasets/items/{item.id}',
        data={'value': 'Renamed', 'order': 7},
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.DATASET_ITEM_UPDATE
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
    assert event.payload == {
        'dataset_id': dataset.id,
        'changed_fields': ['order', 'value'],
    }


def test_partial_update__same_values__no_event(
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
    response = api_client.patch(
        path=f'/datasets/items/{item.id}',
        data={'value': item.value, 'order': item.order},
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert fake_stream.events == []


def test_partial_update__value_too_long__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=1)
    item = dataset.items.get()
    message = 'Ensure this field has no more than 200 characters.'
    partial_update_mock = mocker.patch.object(
        DataSetItemService,
        attribute='partial_update',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.patch(
        path=f'/datasets/items/{item.id}',
        data={'value': 'x' * 201},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'value'
    assert response.data['details']['reason'] == message
    assert fake_stream.events == []
    partial_update_mock.assert_not_called()


def test_partial_update__another_account__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    another_account = create_test_account(name='Another Company')
    dataset = create_test_dataset(account=another_account, items_count=1)
    item = dataset.items.get()
    partial_update_mock = mocker.patch.object(
        DataSetItemService,
        attribute='partial_update',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.patch(
        path=f'/datasets/items/{item.id}',
        data={'value': 'Renamed'},
        format='json',
    )

    # assert
    assert response.status_code == 404
    assert fake_stream.events == []
    partial_update_mock.assert_not_called()


def test_partial_update__service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=2)
    item = dataset.items.get(order=1)
    message = MSG_DS_0002(value='Item 2')
    partial_update_mock = mocker.patch.object(
        DataSetItemService,
        attribute='partial_update',
        side_effect=DataSetServiceException(message=message),
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.patch(
        path=f'/datasets/items/{item.id}',
        data={'value': 'Item 2'},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details'] == {}
    assert fake_stream.events == []
    partial_update_mock.assert_called_once_with(
        force_save=True,
        value='Item 2',
    )
