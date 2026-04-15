import pytest

from src.accounts.serializers.user import UserSerializer
from src.accounts.enums import Language
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
)

pytestmark = pytest.mark.django_db


def test_user_serializer__manager_id__is_account_field():
    """manager_id is an AccountPrimaryKeyRelatedField
    (queryset filtering happens in get_queryset())."""
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)

    serializer = UserSerializer(
        instance=user,
        context={'account': account, 'user': user},
    )

    # assert — field exists and has a base queryset
    field = serializer.fields['manager_id']
    assert field.source == 'manager'
    assert field.queryset is not None


def test_user_serializer__subordinates__is_account_field():
    """subordinates is an AccountPrimaryKeyRelatedField(many=True)."""
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)

    serializer = UserSerializer(
        instance=user,
        context={'account': account, 'user': user},
    )

    # assert
    field = serializer.fields['subordinates']
    assert field.child_relation.queryset is not None


def test_user_serializer__validate__password_to_raw_password():
    """Password field is renamed to raw_password in validate."""
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)

    serializer = UserSerializer(
        instance=user,
        context={'account': account, 'user': user},
    )

    # act
    result = serializer.validate({'password': 'secret123'})

    # assert
    assert 'raw_password' in result
    assert 'password' not in result
    assert result['raw_password'] == 'secret123'


def test_user_serializer__language_choices__ru(mocker):
    """When LANGUAGE_CODE is 'ru', full choices are used."""
    # arrange
    mocker.patch(
        'src.accounts.serializers.user.settings',
    ).LANGUAGE_CODE = Language.ru
    account = create_test_account()
    user = create_test_not_admin(account=account)

    serializer = UserSerializer(
        instance=user,
        context={'account': account, 'user': user},
    )

    # assert
    assert serializer.fields['language'].choices == dict(
        Language.CHOICES,
    )
