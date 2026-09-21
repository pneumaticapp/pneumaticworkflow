import pytest

from src.datasets.models import Dataset
from src.datasets.messages import MSG_DS_0001, MSG_DS_0002
from src.datasets.services.dataset import DataSetService
from src.datasets.services.dataset_item import DataSetItemService
from src.datasets.exceptions import (
    DataSetNameNotUniqueException, DataSetServiceException,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_dataset,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test__create_instance__dataset_created__ok():

    """Dataset created successfully"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    name = 'My Dataset'
    description = 'Test description'
    service = DataSetService(user=user)

    # act
    result = service._create_instance(
        name=name,
        description=description,
    )

    # assert
    assert result == service.instance
    assert result.name == name
    assert result.description == description
    assert result.account == account


def test__create_instance__duplicate_name__raise_exception():

    """Dataset created successfully"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    existent_name = 'My Dataset'
    create_test_dataset(
        account=account,
        name=existent_name,
        items_count=0,
    )
    service = DataSetService(user=user)

    # act
    with pytest.raises(DataSetNameNotUniqueException) as ex:
        service._create_instance(name=existent_name)

    # assert
    assert str(ex.value.message) == str(MSG_DS_0001)


def test__create_instance__default_description__ok():

    """Called with default description"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    name = 'My Dataset'
    service = DataSetService(user=user)

    # act
    result = service._create_instance(name=name)

    # assert
    assert result.name == name
    assert result.description == ''
    assert result.account == account


def test__create_related__items_provided__ok(mocker):

    """items provided"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetService(user=user, instance=dataset)
    items = [
        {'value': 'Item 1', 'order': 1},
        {'value': 'Item 2', 'order': 2},
    ]
    create_items_mock = mocker.patch(
        'src.datasets.services.dataset.DataSetService.create_items',
    )

    # act
    service._create_related(items=items)

    # assert
    create_items_mock.assert_called_once_with(items_data=items)


def test__create_related__items_none__skip(mocker):

    """items is None"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetService(user=user, instance=dataset)
    create_items_mock = mocker.patch(
        'src.datasets.services.dataset.DataSetService.create_items',
    )

    # act
    service._create_related(items=None)

    # assert
    create_items_mock.assert_not_called()


def test_partial_update__all_fields__ok(mocker):

    """items provided"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    old_name = 'Old name'
    old_description = 'Old description'
    dataset = create_test_dataset(
        account=account,
        items_count=0,
        name=old_name,
        description=old_description,
    )
    service = DataSetService(user=user, instance=dataset)
    new_name = 'New name'
    new_description = 'New description'
    items = [
        {'value': 'Item 1', 'order': 1},
    ]
    serialized_data = mocker.Mock()
    dataset_serializer_mock = mocker.patch(
        'src.datasets.services.dataset.DatasetSerializer',
        return_value=mocker.Mock(data=serialized_data),
    )
    send_dataset_updated_notification_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_dataset_updated_notification.delay',
    )
    update_items_mock = mocker.patch(
        'src.datasets.services.dataset.DataSetService.update_items',
    )

    # act
    result = service.partial_update(
        name=new_name,
        description=new_description,
        items=items,
    )

    # assert
    result.refresh_from_db()
    assert result.name == new_name
    assert result.description == new_description
    update_items_mock.assert_called_once_with(items_data=items)
    dataset_serializer_mock.assert_called_once_with(dataset)
    send_dataset_updated_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        dataset_data=serialized_data,
    )


def test_partial_update__items_none__skip(mocker):

    """items is None"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetService(user=user, instance=dataset)
    name = 'New name'

    serialized_data = mocker.Mock()
    dataset_serializer_mock = mocker.patch(
        'src.datasets.services.dataset.DatasetSerializer',
        return_value=mocker.Mock(data=serialized_data),
    )
    send_dataset_updated_notification_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_dataset_updated_notification.delay',
    )
    update_items_mock = mocker.patch(
        'src.datasets.services.dataset.DataSetService.update_items',
    )

    # act
    result = service.partial_update(name=name)

    # assert
    assert result == dataset
    update_items_mock.assert_not_called()
    dataset_serializer_mock.assert_called_once_with(dataset)
    send_dataset_updated_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        dataset_data=serialized_data,
    )


def test_partial_update__duplicate_name__raise_exception(mocker):

    """Rename to existing name in same account raises error"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    existing_name = 'Already Taken'
    create_test_dataset(
        account=account,
        name=existing_name,
        items_count=0,
    )
    dataset = create_test_dataset(
        account=account,
        name='Original Name',
        items_count=0,
    )
    service = DataSetService(user=user, instance=dataset)
    send_dataset_updated_notification_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_dataset_updated_notification.delay',
    )
    update_items_mock = mocker.patch(
        'src.datasets.services.dataset.DataSetService.update_items',
    )

    # act
    with pytest.raises(DataSetNameNotUniqueException) as ex:
        service.partial_update(name=existing_name)

    # assert
    assert str(ex.value.message) == str(MSG_DS_0001)
    send_dataset_updated_notification_mock.assert_not_called()
    update_items_mock.assert_not_called()


def test__delete__ok(mocker):

    """Instance deleted"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    dataset_id = dataset.id
    service = DataSetService(user=user, instance=dataset)
    serialized_data = mocker.Mock()
    dataset_serializer_mock = mocker.patch(
        'src.datasets.services.dataset.DatasetSerializer',
        return_value=mocker.Mock(data=serialized_data),
    )
    send_dataset_deleted_notification_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_dataset_deleted_notification.delay',
    )

    # act
    service.delete()

    # assert
    assert not Dataset.objects.filter(id=dataset_id).exists()
    dataset_serializer_mock.assert_called_once_with(dataset)
    send_dataset_deleted_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        dataset_data=serialized_data,
    )


def test_create_items__ok(mocker):

    """DataSetItemService.__init__
        and DataSetItemService.create called for each item"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetService(user=user, instance=dataset)
    items_data = [
        {'value': 'Item 1', 'order': 1},
        {'value': 'Item 2', 'order': 2},
    ]
    data_set_item_service_init_mock = mocker.patch.object(
        DataSetItemService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.datasets.services.dataset.DataSetItemService.create',
    )

    # act
    service.create_items(items_data=items_data)

    # assert
    assert data_set_item_service_init_mock.call_count == 1
    data_set_item_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=service.is_superuser,
        auth_type=service.auth_type,
    )
    assert create_mock.call_count == 2
    create_mock.assert_has_calls(
        calls=[
            mocker.call(dataset_id=dataset.id, value='Item 1', order=1),
            mocker.call(dataset_id=dataset.id, value='Item 2', order=2),
        ],
        any_order=True,
    )


def test_create_items__empty_list__skip(mocker):

    """Empty items_data — DataSetItemService.create not called"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetService(user=user, instance=dataset)
    data_set_item_service_init_mock = mocker.patch.object(
        DataSetItemService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.datasets.services.dataset.DataSetItemService.create',
    )

    # act
    service.create_items(items_data=[])

    # assert
    data_set_item_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=service.is_superuser,
        auth_type=service.auth_type,
    )
    create_mock.assert_not_called()


def test_update_items__existing_id__partial_update_called(mocker):

    """DataSetItemService.partial_update called for existing item id"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=1)
    existing_item = dataset.items.first()
    service = DataSetService(user=user, instance=dataset)
    items_data = [
        {'id': existing_item.id, 'value': 'Updated', 'order': 99},
    ]
    data_set_item_service_init_mock = mocker.patch.object(
        DataSetItemService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.datasets.services.dataset.'
        'DataSetItemService.partial_update',
    )
    create_mock = mocker.patch(
        'src.datasets.services.dataset.DataSetItemService.create',
    )

    # act
    service.update_items(items_data=items_data)

    # assert
    data_set_item_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=service.is_superuser,
        auth_type=service.auth_type,
        instance=existing_item,
    )
    partial_update_mock.assert_called_once_with(
        value='Updated',
        order=99,
    )
    create_mock.assert_not_called()


def test_update_items__unknown_id__create_called(mocker):

    """DataSetItemService.create called when id is absent or unknown"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetService(user=user, instance=dataset)
    items_data = [
        {'value': 'New Item', 'order': 1},
    ]
    data_set_item_service_init_mock = mocker.patch.object(
        DataSetItemService,
        attribute='__init__',
        return_value=None,
    )
    created_item_mock = mocker.Mock(id=999)
    create_mock = mocker.patch(
        'src.datasets.services.dataset.DataSetItemService.create',
        return_value=created_item_mock,
    )
    partial_update_mock = mocker.patch(
        'src.datasets.services.dataset.'
        'DataSetItemService.partial_update',
    )

    # act
    service.update_items(items_data=items_data)

    # assert
    data_set_item_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=service.is_superuser,
        auth_type=service.auth_type,
    )
    create_mock.assert_called_once_with(
        dataset_id=dataset.id,
        value='New Item',
        order=1,
    )
    partial_update_mock.assert_not_called()


def test_update_items__empty_list__deletes_all(mocker):

    """Empty items_data — all existing items deleted"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=3)
    service = DataSetService(user=user, instance=dataset)
    data_set_item_service_init_mock = mocker.patch.object(
        DataSetItemService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.datasets.services.dataset.'
        'DataSetItemService.partial_update',
    )
    create_mock = mocker.patch(
        'src.datasets.services.dataset.DataSetItemService.create',
    )

    # act
    service.update_items(items_data=[])

    # assert
    data_set_item_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()
    create_mock.assert_not_called()
    assert dataset.items.count() == 0


def test_update_items__mixed__creates_updates_deletes(mocker):

    """Existing updated, new created, obsolete deleted in one call"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=2)
    items = list(dataset.items.order_by('order'))
    service = DataSetService(user=user, instance=dataset)
    items_data = [
        {'id': items[0].id, 'value': 'Updated', 'order': 10},
        {'value': 'Brand New', 'order': 20},
    ]
    data_set_item_service_init_mock = mocker.patch.object(
        DataSetItemService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.datasets.services.dataset.'
        'DataSetItemService.partial_update',
    )
    created_item_mock = mocker.Mock(id=999)
    create_mock = mocker.patch(
        'src.datasets.services.dataset.DataSetItemService.create',
        return_value=created_item_mock,
    )

    # act
    service.update_items(items_data=items_data)

    # assert
    assert data_set_item_service_init_mock.call_count == 2
    data_set_item_service_init_mock.assert_has_calls(
        calls=[
            mocker.call(
                user=user,
                is_superuser=service.is_superuser,
                auth_type=service.auth_type,
                instance=items[0],
            ),
            mocker.call(
                user=user,
                is_superuser=service.is_superuser,
                auth_type=service.auth_type,
            ),
        ],
        any_order=True,
    )
    partial_update_mock.assert_called_once_with(
        value='Updated',
        order=10,
    )
    create_mock.assert_called_once_with(
        dataset_id=dataset.id,
        value='Brand New',
        order=20,
    )
    assert not dataset.items.filter(id=items[1].id).exists()


def test__create__duplicate_dataset_name_same_account__integrity_error():

    """Dataset name must be unique per account (is_deleted=False)"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    duplicate_name = 'My Dataset'
    create_test_dataset(
        account=account,
        name=duplicate_name,
        items_count=0,
    )
    service = DataSetService(user=user)

    # act
    with pytest.raises(DataSetNameNotUniqueException) as ex:
        service._create_instance(name=duplicate_name)

    # assert
    assert str(ex.value.message) == str(MSG_DS_0001)


def test__create__duplicate_dataset_name_different_account__ok():

    """Same dataset name is allowed for different accounts"""

    # arrange
    account_1 = create_test_account(name='Account 1')
    account_2 = create_test_account(name='Account 2')
    user_2 = create_test_owner(account=account_2)
    shared_name = 'My Dataset'
    create_test_dataset(
        account=account_1,
        name=shared_name,
        items_count=0,
    )
    service = DataSetService(user=user_2)

    # act
    result = service._create_instance(name=shared_name)

    # assert
    assert result.name == shared_name
    assert result.account == account_2


def test_create_items__duplicate_value_same_dataset__integrity_error():

    """DatasetItem value must be unique within a dataset (is_deleted=False)"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetService(user=user, instance=dataset)
    value = 'Same Value'
    items_data = [
        {'value': value, 'order': 1},
        {'value': value, 'order': 2},
    ]

    # act
    with pytest.raises(DataSetServiceException) as ex:
        service.create_items(items_data=items_data)

    # assert
    assert ex.value.message == MSG_DS_0002(value=value)


def test_update_items__duplicate_value_same_dataset__integrity_error():

    """Updating two items in the same dataset to the same value raises error"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=2)
    items = list(dataset.items.order_by('order'))
    service = DataSetService(user=user, instance=dataset)
    value = 'Same Value'
    items_data = [
        {'id': items[0].id, 'value': value, 'order': 1},
        {'id': items[1].id, 'value': value, 'order': 2},
    ]

    # act
    with pytest.raises(DataSetServiceException) as ex:
        service.update_items(items_data=items_data)

    # assert
    assert ex.value.message == MSG_DS_0002(value=value)


def test__create_actions__sends_created_notification__ok(mocker):

    """ send_dataset_created_notification.delay
        is called after dataset is created """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetService(user=user, instance=dataset)
    serialized_data = {'id': dataset.id, 'name': dataset.name, 'items': []}
    dataset_serializer_mock = mocker.patch(
        'src.datasets.services.dataset.DatasetSerializer',
        return_value=mocker.Mock(data=serialized_data),
    )
    send_dataset_created_notification_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_dataset_created_notification.delay',
    )

    # act
    service._create_actions()

    # assert
    dataset_serializer_mock.assert_called_once_with(dataset)
    send_dataset_created_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        dataset_data=serialized_data,
    )


def test__create_actions__items__emit_dataset_created(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(
        account=account,
        items_count=0,
    )
    service = DataSetService(
        user=user,
        instance=dataset,
    )
    items = [
        {'value': 'Item 1', 'order': 1},
        {'value': 'Item 2', 'order': 2},
    ]
    serialized_data = mocker.Mock()
    dataset_serializer_mock = mocker.patch(
        'src.datasets.services.dataset.DatasetSerializer',
        return_value=mocker.Mock(data=serialized_data),
    )
    send_dataset_created_notification_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_dataset_created_notification.delay',
    )
    dataset_created_mock = mocker.patch(
        'src.datasets.services.dataset.AuditEventService.dataset_created',
    )

    # act
    service._create_actions(
        name=dataset.name,
        items=items,
    )

    # assert
    dataset_serializer_mock.assert_called_once_with(dataset)
    send_dataset_created_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        dataset_data=serialized_data,
    )
    dataset_created_mock.assert_called_once_with(
        user=user,
        auth_type=service.auth_type,
        dataset=dataset,
        items_count=2,
    )


def test__create_actions__no_items__emit_zero_items_count(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(
        account=account,
        items_count=0,
    )
    service = DataSetService(
        user=user,
        instance=dataset,
    )
    serialized_data = mocker.Mock()
    dataset_serializer_mock = mocker.patch(
        'src.datasets.services.dataset.DatasetSerializer',
        return_value=mocker.Mock(data=serialized_data),
    )
    send_dataset_created_notification_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_dataset_created_notification.delay',
    )
    dataset_created_mock = mocker.patch(
        'src.datasets.services.dataset.AuditEventService.dataset_created',
    )

    # act
    service._create_actions(name=dataset.name)

    # assert
    dataset_serializer_mock.assert_called_once_with(dataset)
    send_dataset_created_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        dataset_data=serialized_data,
    )
    dataset_created_mock.assert_called_once_with(
        user=user,
        auth_type=service.auth_type,
        dataset=dataset,
        items_count=0,
    )


def test_partial_update__name_changed__emit_dataset_updated(mocker):

    """ Items are not named: the rows write their own events. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(
        account=account,
        items_count=0,
        name='Old name',
        description='Same description',
    )
    service = DataSetService(
        user=user,
        instance=dataset,
    )
    items = [{'value': 'Item 1', 'order': 1}]
    serialized_data = mocker.Mock()
    dataset_serializer_mock = mocker.patch(
        'src.datasets.services.dataset.DatasetSerializer',
        return_value=mocker.Mock(data=serialized_data),
    )
    send_dataset_updated_notification_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_dataset_updated_notification.delay',
    )
    update_items_mock = mocker.patch(
        'src.datasets.services.dataset.DataSetService.update_items',
    )
    dataset_updated_mock = mocker.patch(
        'src.datasets.services.dataset.AuditEventService.dataset_updated',
    )

    # act
    service.partial_update(
        name='New name',
        description='Same description',
        items=items,
    )

    # assert
    update_items_mock.assert_called_once_with(items_data=items)
    dataset_serializer_mock.assert_called_once_with(dataset)
    send_dataset_updated_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        dataset_data=serialized_data,
    )
    dataset_updated_mock.assert_called_once_with(
        user=user,
        auth_type=service.auth_type,
        dataset=dataset,
        changed_fields=['name'],
    )


def test_partial_update__same_values__not_emit(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(
        account=account,
        items_count=0,
        name='Same name',
    )
    service = DataSetService(
        user=user,
        instance=dataset,
    )
    items = [{'value': 'Item 1', 'order': 1}]
    serialized_data = mocker.Mock()
    dataset_serializer_mock = mocker.patch(
        'src.datasets.services.dataset.DatasetSerializer',
        return_value=mocker.Mock(data=serialized_data),
    )
    send_dataset_updated_notification_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_dataset_updated_notification.delay',
    )
    update_items_mock = mocker.patch(
        'src.datasets.services.dataset.DataSetService.update_items',
    )
    dataset_updated_mock = mocker.patch(
        'src.datasets.services.dataset.AuditEventService.dataset_updated',
    )

    # act
    service.partial_update(
        name='Same name',
        items=items,
    )

    # assert
    update_items_mock.assert_called_once_with(items_data=items)
    dataset_serializer_mock.assert_called_once_with(dataset)
    send_dataset_updated_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        dataset_data=serialized_data,
    )
    dataset_updated_mock.assert_not_called()


def test__delete__not_used__emit_dataset_deleted(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    service = DataSetService(
        user=user,
        instance=dataset,
    )
    serialized_data = mocker.Mock()
    dataset_serializer_mock = mocker.patch(
        'src.datasets.services.dataset.DatasetSerializer',
        return_value=mocker.Mock(data=serialized_data),
    )
    send_dataset_deleted_notification_mock = mocker.patch(
        'src.notifications.tasks.'
        'send_dataset_deleted_notification.delay',
    )
    dataset_deleted_mock = mocker.patch(
        'src.datasets.services.dataset.AuditEventService.dataset_deleted',
    )

    # act
    service.delete()

    # assert
    dataset_serializer_mock.assert_called_once_with(dataset)
    send_dataset_deleted_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        dataset_data=serialized_data,
    )
    dataset_deleted_mock.assert_called_once_with(
        user=user,
        auth_type=service.auth_type,
        dataset=dataset,
    )


def test_update_items__omitted_item__emit_dataset_item_deleted(mocker):

    """ The omitted rows go in one bulk delete, which passes no
        DataSetItemService: their events are written here. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(
        account=account,
        items_count=2,
    )
    kept_item, omitted_item = dataset.items.order_by('order')
    service = DataSetService(
        user=user,
        instance=dataset,
    )
    partial_update_mock = mocker.patch(
        'src.datasets.services.dataset.'
        'DataSetItemService.partial_update',
    )
    dataset_item_deleted_mock = mocker.patch(
        'src.datasets.services.dataset.'
        'AuditEventService.dataset_item_deleted',
    )

    # act
    service.update_items(
        items_data=[{'id': kept_item.id, 'value': 'Kept', 'order': 1}],
    )

    # assert
    partial_update_mock.assert_called_once_with(
        value='Kept',
        order=1,
    )
    assert not dataset.items.filter(id=omitted_item.id).exists()
    dataset_item_deleted_mock.assert_called_once_with(
        user=user,
        auth_type=service.auth_type,
        item=omitted_item,
    )
