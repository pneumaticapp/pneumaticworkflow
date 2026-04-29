import pytest
from django.conf import settings

from src.notifications.enums import (
    NotificationMethod,
)
from src.notifications.tasks import (
    _send_vacation_delegation_notification,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_send_vacation_delegation_notification__ok(mocker):

    # arrange
    account = create_test_account(logo_lg='https://best.com/logo.jpg')
    user = create_test_owner(
        account=account,
        email='substitute@best.com',
        first_name='Sub',
    )
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_vacation_delegation_notification(
        logging=account.log_api_requests,
        user_id=user.id,
        user_email='substitute@best.com',
        user_first_name=user.first_name,
        account_id=account.id,
        tasks_count=15,
        vacation_owner_name='Bob Smith',
        logo_lg='https://best.com/logo.jpg',
    )

    # assert
    send_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        method_name=NotificationMethod.vacation_delegation,
        user_id=user.id,
        user_email='substitute@best.com',
        user_first_name=user.first_name,
        account_id=account.id,
        tasks_count=15,
        vacation_owner_name='Bob Smith',
        logo_lg='https://best.com/logo.jpg',
        link=f'{settings.FRONTEND_URL}/tasks',
        sync=True,
    )
