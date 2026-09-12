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
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_create__with_items__emit_dataset_create(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    send_dataset_created_notification_mock = mocker.patch(
        'src.datasets.services.dataset.'
        'send_dataset_created_notification.delay',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path='/datasets',
        data={
            'name': 'Clients',
            'items': [
                {'value': 'First', 'order': 1},
                {'value': 'Second', 'order': 2},
            ],
        },
        format='json',
    )

    # assert
    assert response.status_code == 201
    dataset = Dataset.objects.get(id=response.data['id'])
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.DATASET_CREATE
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
    send_dataset_created_notification_mock.assert_called_once_with(
        logging=False,
        account_id=account.id,
        dataset_data=DatasetSerializer(dataset).data,
    )


def test_create__without_items__emit_zero_items_count(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    send_dataset_created_notification_mock = mocker.patch(
        'src.datasets.services.dataset.'
        'send_dataset_created_notification.delay',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path='/datasets',
        data={'name': 'Empty'},
        format='json',
    )

    # assert
    assert response.status_code == 201
    dataset = Dataset.objects.get(id=response.data['id'])
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.DATASET_CREATE
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
    assert event.payload == {'name': 'Empty', 'items_count': 0}
    send_dataset_created_notification_mock.assert_called_once_with(
        logging=False,
        account_id=account.id,
        dataset_data=DatasetSerializer(dataset).data,
    )


def test_create__missing_name__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    message = 'This field is required.'
    create_mock = mocker.patch.object(
        DataSetService,
        attribute='create',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path='/datasets',
        data={},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'name'
    assert response.data['details']['reason'] == message
    assert fake_stream.events == []
    create_mock.assert_not_called()


def test_create__service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    create_mock = mocker.patch.object(
        DataSetService,
        attribute='create',
        side_effect=DataSetNameNotUniqueException(),
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(
        path='/datasets',
        data={'name': 'Taken'},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_DS_0001
    assert response.data['details'] == {}
    assert fake_stream.events == []
    create_mock.assert_called_once_with(
        name='Taken',
        description='',
        items=[],
    )
