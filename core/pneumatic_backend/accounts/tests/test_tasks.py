import pytest
from django.utils import timezone

from pneumatic_backend.accounts.enums import (
    NotificationType,
    NotificationStatus,
)
from pneumatic_backend.accounts.models import (
    SystemMessage,
    Notification,
)
from pneumatic_backend.accounts.tasks import (
    send_system_notification,
)
from pneumatic_backend.accounts.tests.fixtures import (
    create_test_user,
)


pytestmark = pytest.mark.django_db


class TestSendSystemNotification:

    def test_call(self, mocker):
        # arrange
        user = create_test_user()
        another_user = create_test_user(email='another@pneumatic.app')

        send_notification_mock = mocker.patch(
            'pneumatic_backend.accounts.tasks._send_notification'
        )
        SystemMessage.objects.create(
            text='If you smell what The Rock is cooking!',
            publication_date=timezone.now(),
            is_delivery_completed=False,
        )

        # act
        send_system_notification()

        # assert
        assert Notification.objects.filter(user=user).exists()
        assert Notification.objects.filter(user=another_user).exists()
        assert send_notification_mock.call_count == 2

    def test_exists_read_notification__do_not_send_notification(self, mocker):
        # arrange
        user = create_test_user()
        another_user = create_test_user(email='another@pneumatic.app')

        send_notification_mock = mocker.patch(
            'pneumatic_backend.accounts.tasks._send_notification'
        )

        system_message = SystemMessage.objects.create(
            text='If you smell what The Rock is cooking!',
            publication_date=timezone.now(),
            is_delivery_completed=False,
        )
        Notification.objects.create(
            user=another_user,
            system_message=system_message,
            text=system_message.text,
            datetime=system_message.publication_date,
            account=another_user.account,
            status=NotificationStatus.READ,
            type=NotificationType.SYSTEM,
        )

        # act
        send_system_notification()

        # assert
        assert Notification.objects.filter(user=user).exists()
        assert Notification.objects.filter(user=another_user).count() == 1
        assert send_notification_mock.call_count == 1

    def test_is_delivery_completed__do_not_send_notification(self, mocker):
        # arrange
        user = create_test_user()
        another_user = create_test_user(email='another@pneumatic.app')

        send_notification_mock = mocker.patch(
            'pneumatic_backend.accounts.tasks._send_notification'
        )

        SystemMessage.objects.create(
            text='If you smell what The Rock is cooking!',
            publication_date=timezone.now(),
            is_delivery_completed=True,
        )

        # act
        send_system_notification()

        # assert
        assert Notification.objects.filter(user=user).exists() is False
        assert Notification.objects.filter(user=another_user).exists() is False
        send_notification_mock.assert_not_called()
