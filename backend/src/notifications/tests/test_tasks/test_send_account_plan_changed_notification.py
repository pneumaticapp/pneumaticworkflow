import pytest

from src.accounts.enums import UserStatus
from src.notifications.enums import NotificationMethod
from src.notifications.tasks import (
    _send_account_plan_changed_notification,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test__send_account_plan_changed_notification__two_active_users__ok(
    mocker,
):

    """_send_notification called for each active account user"""

    # arrange
    account = create_test_account()
    user_1 = create_test_owner(account=account)
    user_2 = create_test_admin(account=account)
    plan_data = {
        'billing_plan': 'premium',
        'billing_period': 'monthly',
        'plan_expiration': '2026-08-15',
        'plan_expiration_tsp': 1721036800.0,
        'trial_is_active': False,
        'trial_ended': False,
        'is_subscribed': True,
        'active_users': 2,
        'tenants_active_users': 0,
        'max_users': 10,
        'billing_sync': True,
    }

    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_account_plan_changed_notification(
        logging=account.log_api_requests,
        account_id=account.id,
        plan_data=plan_data,
    )

    # assert
    assert send_notification_mock.call_count == 2
    send_notification_mock.assert_has_calls(
        [
            mocker.call(
                method_name=NotificationMethod.account_plan_changed,
                user_id=user_1.id,
                user_email=user_1.email,
                account_id=account.id,
                logging=account.log_api_requests,
                plan_data=plan_data,
                sync=True,
            ),
            mocker.call(
                method_name=NotificationMethod.account_plan_changed,
                user_id=user_2.id,
                user_email=user_2.email,
                account_id=account.id,
                logging=account.log_api_requests,
                plan_data=plan_data,
                sync=True,
            ),
        ],
        any_order=True,
    )


def test__send_account_plan_changed_notification__no_active_users__not_sent(
    mocker,
):

    """_send_notification not called when no active users in account"""

    # arrange
    account = create_test_account()
    create_test_owner(account=account, status=UserStatus.INACTIVE)
    plan_data = {
        'billing_plan': 'premium',
        'billing_period': 'monthly',
        'plan_expiration': '2026-08-15',
        'plan_expiration_tsp': 1721036800.0,
        'trial_is_active': False,
        'trial_ended': False,
        'is_subscribed': True,
        'active_users': 0,
        'tenants_active_users': 0,
        'max_users': 10,
        'billing_sync': True,
    }

    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_account_plan_changed_notification(
        logging=account.log_api_requests,
        account_id=account.id,
        plan_data=plan_data,
    )

    # assert
    send_notification_mock.assert_not_called()
