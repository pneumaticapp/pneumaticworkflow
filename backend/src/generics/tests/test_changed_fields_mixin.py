import pytest

from src.generics.mixins.serializers import ChangedFieldsMixin
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_dataset,
)

pytestmark = pytest.mark.django_db


def test_get_changed_fields__same_value__empty():

    # arrange
    account = create_test_account()
    dataset = create_test_dataset(account=account, name='Clients')
    mixin = ChangedFieldsMixin()
    mixin.instance = dataset
    mixin.validated_data = {'name': 'Clients'}

    # act
    changed_fields = mixin.get_changed_fields()

    # assert
    assert changed_fields == []


def test_get_changed_fields__always_changed_same_value__named():

    """ A relation the request rewrites as a whole is named even when
        it is sent unchanged: its rows are replaced, not compared. """

    # arrange
    account = create_test_account()
    dataset = create_test_dataset(account=account, name='Clients')
    mixin = ChangedFieldsMixin()
    mixin.always_changed_fields = ('name',)
    mixin.instance = dataset
    mixin.validated_data = {'name': 'Clients'}

    # act
    changed_fields = mixin.get_changed_fields()

    # assert
    assert changed_fields == ['name']


def test_get_changed_fields__several_changed__sorted():

    # arrange
    account = create_test_account()
    dataset = create_test_dataset(
        account=account,
        name='Clients',
        description='',
    )
    mixin = ChangedFieldsMixin()
    mixin.instance = dataset
    mixin.validated_data = {
        'name': 'Partners',
        'description': 'Partners of the company',
    }

    # act
    changed_fields = mixin.get_changed_fields()

    # assert
    assert changed_fields == ['description', 'name']
