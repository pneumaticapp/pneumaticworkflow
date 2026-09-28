import pytest

from src.accounts.enums import (
    NotificationStatus,
    NotificationType,
)
from src.accounts.models import Notification
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_read__all_marked__ok(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    n1 = Notification.objects.create(
        user=user,
        account=user.account,
        type=NotificationType.SYSTEM,
        status=NotificationStatus.READ,
    )
    n2 = Notification.objects.create(
        user=user,
        account=user.account,
        type=NotificationType.SYSTEM,
    )
    n3 = Notification.objects.create(
        user=user,
        account=user.account,
        type=NotificationType.COMMENT,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/accounts/notifications/read',
        data={
            'notifications': [n1.id, n2.id, n3.id],
        },
    )

    # assert
    assert response.status_code == 204
    assert user.notifications.exclude_read().exists() is False


def test_read__empty_list__ok(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    Notification.objects.create(
        user=user,
        account=user.account,
        type=NotificationType.COMMENT,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/accounts/notifications/read',
        data={
            'notifications': [],
        },
    )

    # assert
    assert response.status_code == 204
    assert user.notifications.exclude_read().count() == 1


def test_read__not_authenticated__unauthorized(
    api_client,
    identify_mock,
):

    # arrange

    # act
    response = api_client.post(
        '/accounts/notifications/read',
    )

    # assert
    assert response.status_code == 401
