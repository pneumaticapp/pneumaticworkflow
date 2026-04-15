import pytest

from src.datasets.models import DatasetItem
from src.datasets.messages import MSG_DS_0002
from src.datasets.services.dataset_item import DataSetItemService
from src.datasets.exceptions import DataSetServiceException
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_dataset,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test__create_instance__ok():

    """Default call — item created and returned"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=0)
    service = DataSetItemService(user=user)
    value = 'My Option'
    order = 1

    # act
    result = service._create_instance(
        dataset_id=dataset.id,
        value=value,
        order=order,
    )

    # assert
    assert result == service.instance
    assert result.value == value
    assert result.order == order
    assert result.account == account
    assert result.dataset == dataset


def test__create_instance__duplicate_value__raise_exception():

    """IntegrityError raised → DataSetServiceException"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=1)
    service = DataSetItemService(user=user)
    duplicate_value = 'Item 1'

    # act
    with pytest.raises(DataSetServiceException) as ex:
        service._create_instance(
            dataset_id=dataset.id,
            value=duplicate_value,
            order=2,
        )

    # assert
    assert str(ex.value.message) == str(MSG_DS_0002(value=duplicate_value))


def test__partial_update__ok():

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=1)
    item = dataset.items.first()
    service = DataSetItemService(user=user, instance=item)
    new_value = 'Updated Option'
    new_order = 99

    # act
    result = service.partial_update(
        value=new_value,
        order=new_order,
    )

    # assert
    item.refresh_from_db()
    assert result.value == new_value
    assert result.order == new_order


def test__partial_update__duplcate_value__raise_exception():

    """force_save=True, IntegrityError raised → DataSetServiceException"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=2)
    item = dataset.items.get(order=1)
    duplicate_value = 'Item 2'
    service = DataSetItemService(user=user, instance=item)

    # act
    with pytest.raises(DataSetServiceException) as ex:
        service.partial_update(value=duplicate_value)

    # assert
    assert str(ex.value.message) == str(MSG_DS_0002(value=duplicate_value))


def test__delete__ok():

    """Default call — instance deleted"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=1)
    item = dataset.items.first()
    item_id = item.id
    service = DataSetItemService(user=user, instance=item)

    # act
    service.delete()

    # assert
    assert not DatasetItem.objects.filter(id=item_id).exists()
