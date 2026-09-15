import pytest

from src.accounts.enums import UserStatus, UserType
from src.accounts.services.user import UserService
from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    EventObjectType,
    UserEvents,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_deactivate__service_call__emit_user_deactivate(
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
    emit_mock = mocker.patch('src.logs.events.services.emit')
    service = UserService(instance=target, user=owner)

    # act
    service.deactivate()

    # assert
    target.refresh_from_db()
    assert target.status == UserStatus.INACTIVE
    emit_mock.assert_called_once_with(
        UserEvents.DEACTIVATE,
        account_id=account.id,
        actor=Actor(
            id=owner.id,
            email=owner.email,
            user_type=UserType.USER,
        ),
        auth_type=AuthTokenType.USER,
        event_object=EventObject(type=EventObjectType.USER, id=target.id),
        payload={
            'target_email': target.email,
            'status_before': UserStatus.ACTIVE,
        },
        workflow_id=None,
        task_id=None,
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


def test_deactivate__api_key_auth__emit_api_auth_type(
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
    emit_mock = mocker.patch('src.logs.events.services.emit')
    service = UserService(
        instance=target,
        user=owner,
        auth_type=AuthTokenType.API,
    )

    # act
    service.deactivate()

    # assert
    emit_mock.assert_called_once_with(
        UserEvents.DEACTIVATE,
        account_id=account.id,
        actor=Actor(
            id=owner.id,
            email=owner.email,
            user_type=UserType.USER,
        ),
        auth_type=AuthTokenType.API,
        event_object=EventObject(type=EventObjectType.USER, id=target.id),
        payload={
            'target_email': target.email,
            'status_before': UserStatus.ACTIVE,
        },
        workflow_id=None,
        task_id=None,
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


def test_deactivate__no_user__emit_no_actor(
    mocker,
    identify_mock,
    group_mock,
):

    """ A service without a user is a background job, the transfer
        of an account for one: nobody in particular did it. """

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
    emit_mock = mocker.patch('src.logs.events.services.emit')
    service = UserService(account=account, instance=target)

    # act
    service.deactivate(skip_validation=True)

    # assert
    emit_mock.assert_called_once_with(
        UserEvents.DEACTIVATE,
        account_id=account.id,
        actor=None,
        auth_type=None,
        event_object=EventObject(type=EventObjectType.USER, id=target.id),
        payload={
            'target_email': target.email,
            'status_before': UserStatus.ACTIVE,
        },
        workflow_id=None,
        task_id=None,
    )

    # No user, no account analytics: only the target is identified.
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
