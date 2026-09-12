import pytest

from src.datasets.exceptions import DataSetServiceException
from src.datasets.messages import MSG_DS_0001
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


def test_destroy__owner__emit_dataset_delete(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, name='Clients')
    dataset_data = DatasetSerializer(dataset).data
    send_dataset_deleted_notification_mock = mocker.patch(
        'src.datasets.services.dataset.'
        'send_dataset_deleted_notification.delay',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.delete(path=f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.DATASET_DELETE
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
    assert event.payload == {'name': 'Clients'}
    send_dataset_deleted_notification_mock.assert_called_once_with(
        logging=False,
        account_id=account.id,
        dataset_data=dataset_data,
    )


def test_destroy__another_account__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    owner = create_test_owner()
    another_account = create_test_account(name='Another Company')
    dataset = create_test_dataset(account=another_account)
    delete_mock = mocker.patch.object(
        DataSetService,
        attribute='delete',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.delete(path=f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 404
    assert fake_stream.events == []
    delete_mock.assert_not_called()


def test_destroy__service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    delete_mock = mocker.patch.object(
        DataSetService,
        attribute='delete',
        side_effect=DataSetServiceException(message=MSG_DS_0001),
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.delete(path=f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_DS_0001
    assert response.data['details'] == {}
    assert fake_stream.events == []
    delete_mock.assert_called_once_with()
