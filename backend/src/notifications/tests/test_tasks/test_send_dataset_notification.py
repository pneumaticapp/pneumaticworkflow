import pytest

from src.accounts.enums import UserStatus
from src.notifications.enums import NotificationMethod
from src.notifications.tasks import (
    _send_dataset_created_notification,
    _send_dataset_deleted_notification,
    _send_dataset_updated_notification,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test__send_dataset_created_notification__two_active_users__ok(mocker):

    """_send_notification called for each active account user"""

    # arrange
    account = create_test_account()
    user_1 = create_test_owner(account=account)
    user_2 = create_test_admin(account=account)
    dataset_data = {'id': 1, 'name': 'DS', 'items': []}

    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_dataset_created_notification(
        logging=account.log_api_requests,
        account_id=account.id,
        dataset_data=dataset_data,
    )

    # assert
    assert send_notification_mock.call_count == 2
    send_notification_mock.assert_has_calls(
        [
            mocker.call(
                method_name=NotificationMethod.dataset_created,
                account_id=account.id,
                user_id=user_1.id,
                user_email=user_1.email,
                logging=account.log_api_requests,
                dataset_data=dataset_data,
                sync=True,
            ),
            mocker.call(
                method_name=NotificationMethod.dataset_created,
                account_id=account.id,
                user_id=user_2.id,
                user_email=user_2.email,
                logging=account.log_api_requests,
                dataset_data=dataset_data,
                sync=True,
            ),
        ],
        any_order=True,
    )


def test__send_dataset_created_notification__no_active_users__not_sent(mocker):

    """_send_notification not called when no active users in account"""

    # arrange
    account = create_test_account()
    create_test_owner(account=account, status=UserStatus.INACTIVE)
    dataset_data = {'id': 1, 'name': 'DS', 'items': []}

    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_dataset_created_notification(
        logging=account.log_api_requests,
        account_id=account.id,
        dataset_data=dataset_data,
    )

    # assert
    send_notification_mock.assert_not_called()


def test__send_dataset_updated_notification__two_active_users__ok(mocker):

    """_send_notification called for each active account user"""

    # arrange
    account = create_test_account()
    user_1 = create_test_owner(account=account)
    user_2 = create_test_admin(account=account)
    dataset_data = {'id': 1, 'name': 'DS Updated', 'items': []}

    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_dataset_updated_notification(
        logging=account.log_api_requests,
        account_id=account.id,
        dataset_data=dataset_data,
    )

    # assert
    assert send_notification_mock.call_count == 2
    send_notification_mock.assert_has_calls(
        [
            mocker.call(
                method_name=NotificationMethod.dataset_updated,
                account_id=account.id,
                user_id=user_1.id,
                user_email=user_1.email,
                logging=account.log_api_requests,
                dataset_data=dataset_data,
                sync=True,
            ),
            mocker.call(
                method_name=NotificationMethod.dataset_updated,
                account_id=account.id,
                user_id=user_2.id,
                user_email=user_2.email,
                logging=account.log_api_requests,
                dataset_data=dataset_data,
                sync=True,
            ),
        ],
        any_order=True,
    )


def test__send_dataset_updated_notification__no_active_users__not_sent(mocker):

    """_send_notification not called when no active users in account"""

    # arrange
    account = create_test_account()
    create_test_owner(account=account, status=UserStatus.INACTIVE)
    dataset_data = {'id': 1, 'name': 'DS Updated', 'items': []}

    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_dataset_updated_notification(
        logging=account.log_api_requests,
        account_id=account.id,
        dataset_data=dataset_data,
    )

    # assert
    send_notification_mock.assert_not_called()


def test__send_dataset_deleted_notification__two_active_users__ok(mocker):

    """_send_notification called for each active account user"""

    # arrange
    account = create_test_account()
    user_1 = create_test_owner(account=account)
    user_2 = create_test_admin(account=account, email='admin@test.test')
    dataset_data = {'id': 1, 'name': 'DS Deleted', 'items': []}

    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_dataset_deleted_notification(
        logging=account.log_api_requests,
        account_id=account.id,
        dataset_data=dataset_data,
    )

    # assert
    assert send_notification_mock.call_count == 2
    send_notification_mock.assert_has_calls(
        [
            mocker.call(
                method_name=NotificationMethod.dataset_deleted,
                account_id=account.id,
                user_id=user_1.id,
                user_email=user_1.email,
                logging=account.log_api_requests,
                dataset_data=dataset_data,
                sync=True,
            ),
            mocker.call(
                method_name=NotificationMethod.dataset_deleted,
                account_id=account.id,
                user_id=user_2.id,
                user_email=user_2.email,
                logging=account.log_api_requests,
                dataset_data=dataset_data,
                sync=True,
            ),
        ],
        any_order=True,
    )


def test__send_dataset_deleted_notification__no_active_users__not_sent(mocker):

    """_send_notification not called when no active users in account"""

    # arrange
    account = create_test_account()
    create_test_owner(account=account, status=UserStatus.INACTIVE)
    dataset_data = {'id': 1, 'name': 'DS Deleted', 'items': []}

    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_dataset_deleted_notification(
        logging=account.log_api_requests,
        account_id=account.id,
        dataset_data=dataset_data,
    )

    # assert
    send_notification_mock.assert_not_called()
