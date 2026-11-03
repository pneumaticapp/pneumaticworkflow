import pytest

from src.accounts.enums import AbsenceStatus, UserStatus
from src.accounts.messages import MSG_A_0055
from src.accounts.services.exceptions import UserServiceException
from src.accounts.services.user import UserService
from src.accounts.services.vacation import VacationDelegationService
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
    create_test_vacation,
)

pytestmark = pytest.mark.django_db


def test_partial_update__no_request_user__audit_password_set(
    mocker,
    identify_mock,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    service = UserService(
        account=account,
        instance=target,
    )

    # act
    service.partial_update(raw_password='new strong password')

    # assert
    user_updated_mock.assert_called_once_with(
        user=None,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={},
        user_groups=None,
        subordinates=None,
        is_password_set=True,
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_partial_update__group_instances__audit_user_groups(
    mocker,
    identify_mock,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    group = create_test_group(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    service = UserService(
        user=owner,
        instance=target,
    )

    # act
    service.partial_update(user_groups=[group])

    # assert
    user_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={},
        user_groups=[group],
        subordinates=None,
        is_password_set=False,
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_partial_update__subordinates__audit_subordinates(
    mocker,
    identify_mock,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(account=account)
    subordinate = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    service = UserService(
        user=owner,
        instance=target,
    )

    # act
    service.partial_update(subordinates=[subordinate])

    # assert
    subordinate.refresh_from_db()
    assert subordinate.manager_id == target.id
    user_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={},
        user_groups=None,
        subordinates=[subordinate],
        is_password_set=False,
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_partial_update__same_values__audit_update_kwargs(
    mocker,
    identify_mock,
):

    """ A request that arrived is an update, whatever it sent. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    service = UserService(
        user=owner,
        instance=target,
    )

    # act
    service.partial_update(first_name=target.first_name)

    # assert
    user_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
        update_kwargs={'first_name': target.first_name},
        user_groups=None,
        subordinates=None,
        is_password_set=False,
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_partial_update__service_exception__audit_not_called(
    mocker,
    identify_mock,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_updated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_updated',
    )
    service = UserService(
        user=owner,
        instance=target,
    )

    # act
    with pytest.raises(UserServiceException) as ex:
        service.partial_update(
            first_name='New',
            manager=target,
        )

    # assert
    assert ex.value.message == str(MSG_A_0055)
    user_updated_mock.assert_not_called()
    identify_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()


def test_deactivate__absent_user__vacation_deactivated_by_request_user(
    mocker,
    identify_mock,
    group_mock,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(account=account)
    substitute = create_test_not_admin(account=account)
    create_test_vacation(
        user=target,
        substitutes=[substitute],
        absence_status=AbsenceStatus.VACATION,
    )
    identify_users_mock = mocker.patch(
        'src.accounts.services.account.identify_users.delay',
    )
    vacation_delegation_service_init_mock = mocker.patch.object(
        VacationDelegationService,
        attribute='__init__',
        return_value=None,
    )
    vacation_deactivate_mock = mocker.patch.object(
        VacationDelegationService,
        attribute='deactivate',
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
        user=owner,
        instance=target,
    )

    # act
    service.deactivate()

    # assert
    target.refresh_from_db()
    assert target.status == UserStatus.INACTIVE
    vacation_delegation_service_init_mock.assert_called_once_with(
        target,
        request_user=owner,
        auth_type=AuthTokenType.USER,
    )
    vacation_deactivate_mock.assert_called_once_with()
    user_deactivated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
    )
    identify_mock.assert_called_once_with(target)
    group_mock.assert_called_once_with(
        user=target,
        account=account,
    )
    identify_users_mock.assert_called_once_with(
        user_ids=(owner.id, substitute.id),
    )
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
