import pytest

from src.datasets.exceptions import DataSetNameNotUniqueException
from src.datasets.messages import MSG_DS_0001
from src.datasets.models import Dataset
from src.datasets.serializers import DatasetSerializer
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


def test_partial_update__name_and_items__emit_changed_fields(
    mocker,
    api_client,
    fake_stream,
):

    """ The rows are named whenever they are sent, even unchanged: the
        request replaces them all. An equal description is left out. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(
        account=account,
        name='Old name',
        description='Desc',
        items_count=1,
    )
    item = dataset.items.get()
    send_dataset_updated_notification_mock = mocker.patch(
        'src.datasets.services.dataset.'
        'send_dataset_updated_notification.delay',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.patch(
        path=f'/datasets/{dataset.id}',
        data={
            'name': 'New name',
            'description': 'Desc',
            'items': [
                {'id': item.id, 'value': item.value, 'order': item.order},
            ],
        },
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.DATASET_UPDATE
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
    assert event.payload == {
        'name': 'New name',
        'changed_fields': ['items', 'name'],
    }
    send_dataset_updated_notification_mock.assert_called_once_with(
        logging=False,
        account_id=account.id,
        dataset_data=DatasetSerializer(
            Dataset.objects.get(id=dataset.id),
        ).data,
    )


def test_partial_update__description_changed__emit_stored_name(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(
        account=account,
        name='Clients',
        description='Old',
    )
    send_dataset_updated_notification_mock = mocker.patch(
        'src.datasets.services.dataset.'
        'send_dataset_updated_notification.delay',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.patch(
        path=f'/datasets/{dataset.id}',
        data={'name': 'Clients', 'description': 'New'},
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.DATASET_UPDATE
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
    assert event.payload == {
        'name': 'Clients',
        'changed_fields': ['description'],
    }
    send_dataset_updated_notification_mock.assert_called_once_with(
        logging=False,
        account_id=account.id,
        dataset_data=DatasetSerializer(
            Dataset.objects.get(id=dataset.id),
        ).data,
    )


def test_partial_update__same_values__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(
        account=account,
        name='Clients',
        description='Desc',
    )
    send_dataset_updated_notification_mock = mocker.patch(
        'src.datasets.services.dataset.'
        'send_dataset_updated_notification.delay',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.patch(
        path=f'/datasets/{dataset.id}',
        data={'name': 'Clients', 'description': 'Desc'},
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert fake_stream.events == []
    send_dataset_updated_notification_mock.assert_called_once_with(
        logging=False,
        account_id=account.id,
        dataset_data=DatasetSerializer(
            Dataset.objects.get(id=dataset.id),
        ).data,
    )


def test_partial_update__name_too_long__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    message = 'Ensure this field has no more than 200 characters.'
    partial_update_mock = mocker.patch.object(
        DataSetService,
        attribute='partial_update',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.patch(
        path=f'/datasets/{dataset.id}',
        data={'name': 'x' * 201},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'name'
    assert response.data['details']['reason'] == message
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
    dataset = create_test_dataset(account=account, name='Clients')
    partial_update_mock = mocker.patch.object(
        DataSetService,
        attribute='partial_update',
        side_effect=DataSetNameNotUniqueException(),
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.patch(
        path=f'/datasets/{dataset.id}',
        data={'name': 'Taken'},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_DS_0001
    assert response.data['details'] == {}
    assert fake_stream.events == []
    partial_update_mock.assert_called_once_with(name='Taken')
