import pytest
from src.authentication.serializers import ContextUserSerializer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
)

pytestmark = pytest.mark.django_db


def test_context_user_serializer__report_ids__ok():
    # arrange
    account = create_test_account()
    manager = create_test_not_admin(account=account)
    report = create_test_not_admin(account=account, email='rep@test.test')
    manager.subordinates.set([report])

    # act
    serializer = ContextUserSerializer(instance=manager)
    data = serializer.data

    # assert
    assert data['report_ids'] == [report.id]
    assert data['manager_id'] is None


def test_context_user_serializer__manager_id__ok():
    # arrange
    account = create_test_account()
    manager = create_test_not_admin(account=account)
    user = create_test_not_admin(account=account, email='user@test.test')
    user.manager = manager
    user.save()

    # act
    serializer = ContextUserSerializer(instance=user)
    data = serializer.data

    # assert
    assert data['manager_id'] == manager.id
    assert data['report_ids'] == []
