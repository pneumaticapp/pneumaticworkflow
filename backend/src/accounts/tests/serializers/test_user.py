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
    """Assigning a user's ancestor as subordinate must raise MSG_A_0050.

    Since cycle detection now lives in *validate()* (which has access
    to the proposed manager), this test exercises the cross-field path.
    """
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
        serializer.validate({'subordinates': [manager]})

    # assert
    assert ex.value.detail[0] == MSG_A_0050


def test_user_serializer__validate__manager_null_subordinate_old_manager__ok():
    """When manager_id is set to None *and* the old manager is listed
    as subordinate in the same request, the result is non-cyclic
    (B -> A with no upward chain) and must be accepted.
    """
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

    # act — manager=None breaks the old chain, [manager] is a valid sub
    result = serializer.validate({
        'manager': None,
        'subordinates': [manager],
    })

    # assert
    assert result['subordinates'] == [manager]


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
