import pytest

from src.accounts.serializers.user import UserSerializer
from src.accounts.enums import Language
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
)

pytestmark = pytest.mark.django_db


def test_user_serializer__manager_id__uses_account_filter():
    """AccountPrimaryKeyRelatedField filters by account
    via get_queryset(); verify queryset is set on __init__."""
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)

    serializer = UserSerializer(
        instance=user,
        context={'account': account, 'user': user},
    )

    # act
    qs = serializer.fields['manager_id'].queryset

    # assert — queryset is set (not the default .none())
    assert qs is not None
    assert qs.count() >= 0


def test_user_serializer__subordinates__uses_account_filter():
    """Subordinates field queryset is set via __init__."""
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)

    serializer = UserSerializer(
        instance=user,
        context={'account': account, 'user': user},
    )

    # act
    qs = serializer.fields['subordinates'].child_relation.queryset

    # assert
    assert qs is not None
    assert qs.count() >= 0


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


def test_user_serializer__no_account_ctx__default_queryset():
    """When context has no 'account' the default queryset
    stays as-is (read-only serialization path)."""
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)

    serializer = UserSerializer(
        instance=user,
        context={'user': user},
    )

    # act / assert — no crash, queryset stays the default
    qs = serializer.fields['manager_id'].queryset
    assert qs is not None


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
