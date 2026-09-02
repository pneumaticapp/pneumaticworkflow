import pytest

from src.accounts.enums import NotificationType
from src.accounts.models import Notification
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_delete__ok(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    notification = Notification.objects.create(
        user=user,
        account=user.account,
        type=NotificationType.SYSTEM,
    )

    # act
    response = api_client.delete(f'/accounts/notifications/{notification.id}')

    # assert
    assert response.status_code == 204
    assert Notification.objects.filter(id=notification.id).exists() is False


def test_delete__not_exist__not_found(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.delete('/accounts/notifications/99999')

    # assert
    assert response.status_code == 404
