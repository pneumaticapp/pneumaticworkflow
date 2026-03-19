import pytest

from src.processes.models.dataset import Dataset
from src.processes.services.dataset import DataSetService
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


def test__create_items__bulk_created__ok():

    """Items bulk created from items_data"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetService(user=user, instance=dataset)
    items_data = [
        {'value': 'Item 1', 'order': 1},
        {'value': 'Item 2', 'order': 2},
    ]

    # act
    service._create_items(items_data=items_data)

    # assert
    items = list(dataset.items.order_by('order'))
    assert len(items) == 2
    assert items[0].value == 'Item 1'
    assert items[0].order == 1
    assert items[1].value == 'Item 2'
    assert items[1].order == 2


def test__update_items__existing_id__ok():

    """Existing item updated (id matches)"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=1)
    existing_item = dataset.items.first()
    service = DataSetService(user=user, instance=dataset)
    items_data = [
        {'id': existing_item.id, 'value': 'Updated Value', 'order': 10},
    ]

    # act
    service._update_items(items_data=items_data)

    # assert
    existing_item.refresh_from_db()
    assert existing_item.value == 'Updated Value'
    assert existing_item.order == 10
    assert dataset.items.count() == 1


def test__update_items__new_id__ok():

    """New item created (id absent or unknown)"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetService(user=user, instance=dataset)
    items_data = [
        {'value': 'New Item', 'order': 1},
    ]

    # act
    service._update_items(items_data=items_data)

    # assert
    created_item = dataset.items.first()
    assert dataset.items.count() == 1
    assert created_item.value == 'New Item'
    assert created_item.order == 1


def test__update_items__obsolete_items__deleted():

    """Obsolete items deleted"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=2)
    items = list(dataset.items.order_by('order'))
    service = DataSetService(user=user, instance=dataset)

    # Keep only the first item in incoming data
    items_data = [
        {'id': items[0].id, 'value': items[0].value, 'order': items[0].order},
    ]

    # act
    service._update_items(items_data=items_data)

    # assert
    assert dataset.items.count() == 1
    assert dataset.items.filter(id=items[0].id).exists()
    assert not dataset.items.filter(id=items[1].id).exists()


def test__update_items__no_obsolete_items__skip():

    """No items to delete"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=1)
    existing_item = dataset.items.first()
    service = DataSetService(user=user, instance=dataset)
    items_data = [
        {
            'id': existing_item.id,
            'value': existing_item.value,
            'order': existing_item.order,
        },
    ]

    # act
    service._update_items(items_data=items_data)

    # assert
    assert dataset.items.count() == 1
    assert dataset.items.filter(id=existing_item.id).exists()


def test__update_items__no_items_to_update__skip():

    """No items to update"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetService(user=user, instance=dataset)

    # All incoming items are new (no id) — items_to_update stays empty
    items_data = [
        {'value': 'First', 'order': 1},
        {'value': 'Second', 'order': 2},
    ]

    # act
    service._update_items(items_data=items_data)

    # assert
    items = list(dataset.items.order_by('order'))
    assert len(items) == 2
    assert items[0].value == 'First'
    assert items[1].value == 'Second'


def test__update_items__no_items_to_create__skip():

    """No items to create"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=2)
    items = list(dataset.items.order_by('order'))
    service = DataSetService(user=user, instance=dataset)

    # All incoming items match existing ids — items_to_create stays empty
    items_data = [
        {'id': items[0].id, 'value': 'Updated First', 'order': 10},
        {'id': items[1].id, 'value': 'Updated Second', 'order': 20},
    ]

    # act
    service._update_items(items_data=items_data)

    # assert
    items[0].refresh_from_db()
    items[1].refresh_from_db()
    assert dataset.items.count() == 2
    assert items[0].value == 'Updated First'
    assert items[1].value == 'Updated Second'


def test__delete__instance__ok():

    """Instance deleted"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    dataset_id = dataset.id
    service = DataSetService(user=user, instance=dataset)

    # act
    service.delete()

    # assert
    assert not Dataset.objects.filter(id=dataset_id).exists()


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

    _create_items_mock = mocker.patch.object(service, '_create_items')

    # act
    service._create_related(items=items)

    # assert
    _create_items_mock.assert_called_once_with(items_data=items)


def test__create_related__items_none__skip(mocker):

    """items is None"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetService(user=user, instance=dataset)

    _create_items_mock = mocker.patch.object(service, '_create_items')

    # act
    service._create_related(items=None)

    # assert
    _create_items_mock.assert_not_called()


def test__create_related__default_params__ok(mocker):

    """Called with default parameters"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetService(user=user, instance=dataset)

    _create_items_mock = mocker.patch.object(service, '_create_items')

    # act
    service._create_related()

    # assert
    _create_items_mock.assert_not_called()


def test__partial_update__items_provided__ok(mocker):

    """items provided"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetService(user=user, instance=dataset)
    items = [
        {'value': 'Item 1', 'order': 1},
    ]

    _update_items_mock = mocker.patch.object(service, '_update_items')

    # act
    result = service.partial_update(items=items)

    # assert
    assert result == dataset
    _update_items_mock.assert_called_once_with(items_data=items)


def test__partial_update__items_none__skip(mocker):

    """items is None"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetService(user=user, instance=dataset)

    _update_items_mock = mocker.patch.object(service, '_update_items')

    # act
    result = service.partial_update()

    # assert
    assert result == dataset
    _update_items_mock.assert_not_called()


def test__partial_update__default_force_save__ok(mocker):

    """Called with default force_save"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetService(user=user, instance=dataset)
    old_name = dataset.name
    new_name = 'Updated Name'

    _update_items_mock = mocker.patch.object(service, '_update_items')

    # act
    service.partial_update(name=new_name)

    # assert
    dataset.refresh_from_db()
    assert dataset.name == old_name
    _update_items_mock.assert_not_called()
