import pytest

from src.accounts import messages
from src.accounts.enums import UserStatus
from src.accounts.services.exceptions import (
    PreventAccountOwnerDeletion,
    PreventSelfDeletion,
)
from src.accounts.services.user import UserService
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_deactivate__service_call__audit_user_deactivated(
    mocker,
    identify_mock,
    group_mock,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(account=account)
    identify_users_mock = mocker.patch(
        'src.accounts.services.account.identify_users.delay',
    )
    send_user_deactivated_mock = mocker.patch(
        'src.notifications.tasks.send_user_deactivated_notification.delay',
    )
    send_user_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_user_deleted_notification.delay',
    )
    user_deactivated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_deactivated',
    )
    service = UserService(
        instance=target,
        user=owner,
    )

    # act
    service.deactivate()

    # assert
    target.refresh_from_db()
    assert target.status == UserStatus.INACTIVE
    user_deactivated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
    )
    identify_mock.assert_called_once_with(target)

    # The deactivated person is no longer among the users the account
    # service tells the analytics about.
    identify_users_mock.assert_called_once_with(user_ids=(owner.id,))
    group_mock.assert_called_once_with(user=target, account=account)
    send_user_deactivated_mock.assert_called_once_with(
        user_id=target.id,
        user_email=target.email,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    send_user_deleted_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_deactivate__api_key_auth__audit_api_auth_type(
    mocker,
    identify_mock,
    group_mock,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(account=account)
    identify_users_mock = mocker.patch(
        'src.accounts.services.account.identify_users.delay',
    )
    send_user_deactivated_mock = mocker.patch(
        'src.notifications.tasks.send_user_deactivated_notification.delay',
    )
    send_user_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_user_deleted_notification.delay',
    )
    user_deactivated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_deactivated',
    )
    service = UserService(
        instance=target,
        user=owner,
        auth_type=AuthTokenType.API,
    )

    # act
    service.deactivate()

    # assert
    user_deactivated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.API,
        target=target,
    )
    identify_mock.assert_called_once_with(target)
    identify_users_mock.assert_called_once_with(user_ids=(owner.id,))
    group_mock.assert_called_once_with(user=target, account=account)
    send_user_deactivated_mock.assert_called_once_with(
        user_id=target.id,
        user_email=target.email,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    send_user_deleted_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_deactivate__no_user__audit_user_none(
    mocker,
    identify_mock,
    group_mock,
):

    """ The service takes no user (BaseModelService makes it
        optional), and then the record has no actor. No caller does
        that today: the account transfer passes user=prev_user. """

    # arrange
    account = create_test_account()
    target = create_test_admin(account=account)
    identify_users_mock = mocker.patch(
        'src.accounts.services.account.identify_users.delay',
    )
    send_user_deactivated_mock = mocker.patch(
        'src.notifications.tasks.send_user_deactivated_notification.delay',
    )
    send_user_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_user_deleted_notification.delay',
    )
    user_deactivated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_deactivated',
    )
    service = UserService(
        account=account,
        instance=target,
    )

    # act
    service.deactivate(skip_validation=True)

    # assert
    user_deactivated_mock.assert_called_once_with(
        user=None,
        auth_type=AuthTokenType.USER,
        target=target,
    )

    # The account analytics run with the target as the user; nobody
    # active is left in the account, so the list of users is empty.
    identify_mock.assert_called_once_with(target)
    identify_users_mock.assert_called_once_with(user_ids=())
    group_mock.assert_called_once_with(user=target, account=account)
    send_user_deactivated_mock.assert_called_once_with(
        user_id=target.id,
        user_email=target.email,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    send_user_deleted_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_deactivate__self__audit_not_called(mocker):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    admin = create_test_admin(account=account)
    send_user_deactivated_mock = mocker.patch(
        'src.notifications.tasks.send_user_deactivated_notification.delay',
    )
    send_user_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_user_deleted_notification.delay',
    )
    user_deactivated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_deactivated',
    )
    service = UserService(
        instance=admin,
        user=admin,
    )

    # act
    with pytest.raises(PreventSelfDeletion) as ex:
        service.deactivate()

    # assert
    assert ex.value.message == str(messages.MSG_A_0047)
    admin.refresh_from_db()
    assert admin.status == UserStatus.ACTIVE
    user_deactivated_mock.assert_not_called()
    send_user_deactivated_mock.assert_not_called()
    send_user_deleted_mock.assert_not_called()


def test_deactivate__account_owner__audit_not_called(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    admin = create_test_admin(account=account)
    send_user_deactivated_mock = mocker.patch(
        'src.notifications.tasks.send_user_deactivated_notification.delay',
    )
    send_user_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_user_deleted_notification.delay',
    )
    user_deactivated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_deactivated',
    )
    service = UserService(
        instance=owner,
        user=admin,
    )

    # act
    with pytest.raises(PreventAccountOwnerDeletion) as ex:
        service.deactivate()

    # assert
    assert ex.value.message == str(messages.MSG_A_0048)
    owner.refresh_from_db()
    assert owner.status == UserStatus.ACTIVE
    user_deactivated_mock.assert_not_called()
    send_user_deactivated_mock.assert_not_called()
    send_user_deleted_mock.assert_not_called()
