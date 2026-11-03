import pytest

from src.accounts import messages
from src.accounts.enums import UserStatus
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_not_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_delete__deprecated_endpoint__audit_user_deactivated(
    mocker,
    identify_mock,
    group_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(account=account)
    api_client.token_authenticate(owner)
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

    # act
    response = api_client.post(f'/accounts/users/{target.id}/delete')

    # assert
    assert response.status_code == 204
    user_deactivated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
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


def test_delete__last_performer__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(account=account)
    api_client.token_authenticate(owner)
    user_is_last_performer_mock = mocker.patch(
        'src.accounts.services.user.user_is_last_performer',
        return_value=True,
    )
    user_deactivated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_deactivated',
    )

    # act
    response = api_client.post(f'/accounts/users/{target.id}/delete')

    # assert
    assert response.status_code == 400
    assert response.data == {
        'code': ErrorCode.VALIDATION_ERROR,
        'message': messages.MSG_A_0011,
        'details': {},
    }
    target.refresh_from_db()
    assert target.status == UserStatus.ACTIVE
    user_is_last_performer_mock.assert_called_once_with(target)
    user_deactivated_mock.assert_not_called()


def test_delete__not_admin__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    target = create_test_admin(account=account)
    api_client.token_authenticate(user)
    user_deactivated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_deactivated',
    )

    # act
    response = api_client.post(f'/accounts/users/{target.id}/delete')

    # assert
    assert response.status_code == 403
    target.refresh_from_db()
    assert target.status == UserStatus.ACTIVE
    user_deactivated_mock.assert_not_called()


def test_delete__another_account_user__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    another_account = create_test_account(name='Other')
    target = create_test_admin(
        account=another_account,
        email='another@test.test',
    )
    api_client.token_authenticate(owner)
    user_deactivated_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_deactivated',
    )

    # act
    response = api_client.post(f'/accounts/users/{target.id}/delete')

    # assert
    assert response.status_code == 404
    target.refresh_from_db()
    assert target.status == UserStatus.ACTIVE
    user_deactivated_mock.assert_not_called()
