import pytest
from rest_framework.exceptions import ValidationError

from src.accounts.serializers.user import UserSerializer
from src.accounts.messages import MSG_A_0049, MSG_A_0050
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
)

pytestmark = pytest.mark.django_db


def test_user_serializer__validate_manager_id__ok():
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    manager = create_test_not_admin(account=account, email='manager@test.test')

    serializer = UserSerializer(
        instance=user,
        context={'account': account, 'user': user},
    )

    # act
    result = serializer.validate_manager_id(manager)

    # assert
    assert result == manager


def test_user_serializer__validate_manager_id__self_assignment__error():
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)

    serializer = UserSerializer(
        instance=user,
        context={'account': account, 'user': user},
    )

    # act
    with pytest.raises(ValidationError) as ex:
        serializer.validate_manager_id(user)

    # assert
    assert ex.value.detail[0] == MSG_A_0049


def test_user_serializer__validate_manager_id__circular__error():
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    manager = create_test_not_admin(account=account, email='manager@test.test')
    manager.manager = user
    manager.save()

    serializer = UserSerializer(
        instance=user,
        context={'account': account, 'user': user},
    )

    # act
    with pytest.raises(ValidationError) as ex:
        serializer.validate_manager_id(manager)

    # assert
    assert ex.value.detail[0] == MSG_A_0050


def test_user_serializer__validate_subordinates__ok():
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    report1 = create_test_not_admin(account=account, email='rep1@test.test')
    report2 = create_test_not_admin(account=account, email='rep2@test.test')

    serializer = UserSerializer(
        instance=user,
        context={'account': account, 'user': user},
    )

    # act
    result = serializer.validate_subordinates([report1, report2])

    # assert
    assert result == [report1, report2]


def test_user_serializer__validate_subordinates__self__error():
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)

    serializer = UserSerializer(
        instance=user,
        context={'account': account, 'user': user},
    )

    # act
    with pytest.raises(ValidationError) as ex:
        serializer.validate_subordinates([user])

    # assert
    assert ex.value.detail[0] == MSG_A_0049


def test_user_serializer__validate_subordinates__circular__error():
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    manager = create_test_not_admin(account=account, email='manager@test.test')
    user.manager = manager
    user.save()

    serializer = UserSerializer(
        instance=user,
        context={'account': account, 'user': user},
    )

    # act
    with pytest.raises(ValidationError) as ex:
        serializer.validate_subordinates([manager])

    # assert
    assert ex.value.detail[0] == MSG_A_0050


def test_user_serializer__validate_manager_id__null__ok():
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)

    serializer = UserSerializer(
        instance=user,
        context={'account': account, 'user': user},
    )

    # act
    result = serializer.validate_manager_id(None)

    # assert
    assert result is None
