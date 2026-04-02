import pytest
from rest_framework.exceptions import ValidationError

from src.accounts.serializers.user import (
    SetManagerSerializer,
    SetReportsSerializer,
)
from src.accounts.messages import MSG_A_0049, MSG_A_0050
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
)

pytestmark = pytest.mark.django_db


def test_set_manager_serializer__ok():
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    manager = create_test_not_admin(account=account, email='manager@test.test')

    serializer = SetManagerSerializer(
        instance=user, context={'account': account},
    )

    # act
    result = serializer.validate_manager_id(manager)

    # assert
    assert result == manager


def test_set_manager_serializer__self_assignment__validation_error():
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)

    serializer = SetManagerSerializer(
        instance=user, context={'account': account},
    )

    # act
    with pytest.raises(ValidationError) as ex:
        serializer.validate_manager_id(user)

    # assert
    assert ex.value.detail[0] == MSG_A_0049


def test_set_manager_serializer__circular_hierarchy__validation_error():
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    manager = create_test_not_admin(account=account, email='manager@test.test')
    manager.manager = user
    manager.save()

    serializer = SetManagerSerializer(
        instance=user, context={'account': account},
    )

    # act
    with pytest.raises(ValidationError) as ex:
        serializer.validate_manager_id(manager)

    # assert
    assert ex.value.detail[0] == MSG_A_0050


def test_set_reports_serializer__ok():
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    report1 = create_test_not_admin(account=account, email='rep1@test.test')
    report2 = create_test_not_admin(account=account, email='rep2@test.test')

    serializer = SetReportsSerializer(
        instance=user, context={'account': account},
    )

    # act
    result = serializer.validate_report_ids([report1, report2])

    # assert
    assert result == [report1, report2]


def test_set_reports_serializer__self_assignment__validation_error():
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)

    serializer = SetReportsSerializer(
        instance=user, context={'account': account},
    )

    # act
    with pytest.raises(ValidationError) as ex:
        serializer.validate_report_ids([user])

    # assert
    assert ex.value.detail[0] == MSG_A_0049


def test_set_reports_serializer__circular_hierarchy__validation_error():
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    manager = create_test_not_admin(account=account, email='manager@test.test')
    user.manager = manager
    user.save()

    serializer = SetReportsSerializer(
        instance=user, context={'account': account},
    )

    # act
    with pytest.raises(ValidationError) as ex:
        serializer.validate_report_ids([manager])

    # assert
    assert ex.value.detail[0] == MSG_A_0050
