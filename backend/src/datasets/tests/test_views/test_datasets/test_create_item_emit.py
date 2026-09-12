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


def test_create_item__valid__emit_dataset_item_create(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path=f'/datasets/{dataset.id}/item',
        data={'value': 'New', 'order': 5},
        format='json',
    )

    # assert
    assert response.status_code == 201
    item = dataset.items.get()
    assert response.data['id'] == item.id
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.DATASET_ITEM_CREATE
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


def test_create_item__missing_value__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    message = 'This field is required.'
    create_mock = mocker.patch.object(
        DataSetItemService,
        attribute='create',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path=f'/datasets/{dataset.id}/item',
        data={'order': 5},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'value'
    assert response.data['details']['reason'] == message
    assert fake_stream.events == []
    create_mock.assert_not_called()


def test_create_item__another_account__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    another_account = create_test_account(name='Another Company')
    dataset = create_test_dataset(account=another_account)
    create_mock = mocker.patch.object(
        DataSetItemService,
        attribute='create',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path=f'/datasets/{dataset.id}/item',
        data={'value': 'New', 'order': 5},
        format='json',
    )

    # assert
    assert response.status_code == 404
    assert fake_stream.events == []
    create_mock.assert_not_called()


def test_create_item__service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    message = MSG_DS_0002(value='Item 1')
    create_mock = mocker.patch.object(
        DataSetItemService,
        attribute='create',
        side_effect=DataSetServiceException(message=message),
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path=f'/datasets/{dataset.id}/item',
        data={'value': 'Item 1', 'order': 5},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details'] == {}
    assert fake_stream.events == []
    create_mock.assert_called_once_with(
        dataset_id=dataset.id,
        value='Item 1',
        order=5,
    )
