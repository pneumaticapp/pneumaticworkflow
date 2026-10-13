import pytest

from src.accounts.enums import (
    NotificationStatus,
    NotificationType,
)
from src.accounts.models import Notification
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_count__filter_new__ok(api_client):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    Notification.objects.create(
        user=user,
        account=user.account,
        type=NotificationType.SYSTEM,
        status=NotificationStatus.READ,
    )
    Notification.objects.create(
        user=user,
        account=user.account,
        type=NotificationType.SYSTEM,
    )

    # act
    response = api_client.get(
        '/accounts/notifications/count',
        data={'status': NotificationStatus.NEW},
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 1
