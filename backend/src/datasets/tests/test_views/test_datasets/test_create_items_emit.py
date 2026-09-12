import pytest

from src.datasets.exceptions import DataSetServiceException
from src.datasets.messages import MSG_DS_0002
from src.datasets.services.dataset import DataSetService
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


def test_create_items__two_items__emit_dataset_items_add(
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(
        account=account,
        name='Clients',
        items_count=1,
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path=f'/datasets/{dataset.id}/items',
        data=[
            {'value': 'New 1', 'order': 2},
            {'value': 'New 2', 'order': 3},
        ],
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert dataset.items.count() == 3
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.DATASET_ITEMS_ADD
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.DATASET,
        id=dataset.id,
    )
    assert event.payload == {'name': 'Clients', 'items_count': 2}


def test_create_items__value_too_long__no_event(
    mocker,
    api_client,
    fake_stream,
):

    """ A body of many=True is validated by the ListSerializer of the
        framework, which does not carry the custom is_valid of the
        project: the error keeps the enriched framework format instead
        of {message, code, details}. Asserted as the endpoint answers
        today. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    message = 'Ensure this field has no more than 200 characters.'
    create_items_mock = mocker.patch.object(
        DataSetService,
        attribute='create_items',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path=f'/datasets/{dataset.id}/items',
        data=[{'value': 'x' * 201}],
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data[0]['value'][0]['message__'] == message
    assert response.data[0]['value'][0]['name__'] == 'value'
    assert fake_stream.events == []
    create_items_mock.assert_not_called()


def test_create_items__another_account__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    another_account = create_test_account(name='Another Company')
    dataset = create_test_dataset(account=another_account)
    create_items_mock = mocker.patch.object(
        DataSetService,
        attribute='create_items',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path=f'/datasets/{dataset.id}/items',
        data=[{'value': 'New', 'order': 1}],
        format='json',
    )

    # assert
    assert response.status_code == 404
    assert fake_stream.events == []
    create_items_mock.assert_not_called()


def test_create_items__service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    message = MSG_DS_0002(value='Item 1')
    create_items_mock = mocker.patch.object(
        DataSetService,
        attribute='create_items',
        side_effect=DataSetServiceException(message=message),
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path=f'/datasets/{dataset.id}/items',
        data=[{'value': 'Item 1', 'order': 1}],
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details'] == {}
    assert fake_stream.events == []
    create_items_mock.assert_called_once_with(
        items_data=[{'value': 'Item 1', 'order': 1}],
    )
