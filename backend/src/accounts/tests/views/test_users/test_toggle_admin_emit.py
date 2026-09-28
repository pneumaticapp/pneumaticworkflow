import pytest

from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_toggle_admin__grant__audit_user_admin_toggled(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    api_client.token_authenticate(owner)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_admin_toggled_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_admin_toggled',
    )

    # act
    response = api_client.post(
        f'/accounts/users/{target.id}/toggle-admin',
    )

    # assert
    assert response.status_code == 204
    target.refresh_from_db()
    assert target.is_admin is True
    user_admin_toggled_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=owner.account_id,
        user_data=mocker.ANY,
    )


def test_toggle_admin__revoke__audit_user_admin_toggled(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(account=account)
    api_client.token_authenticate(owner)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_admin_toggled_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_admin_toggled',
    )

    # act
    response = api_client.post(
        f'/accounts/users/{target.id}/toggle-admin',
    )

    # assert
    assert response.status_code == 204
    target.refresh_from_db()
    assert target.is_admin is False
    user_admin_toggled_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=target,
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=owner.account_id,
        user_data=mocker.ANY,
    )


def test_toggle_admin__not_admin__audit_not_called(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    target = create_test_not_admin(
        account=account,
        email='target@test.test',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_admin_toggled_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_admin_toggled',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(f'/accounts/users/{target.id}/toggle-admin')

    # assert
    assert response.status_code == 403
    target.refresh_from_db()
    assert target.is_admin is False
    user_admin_toggled_mock.assert_not_called()
    identify_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()


def test_toggle_admin__user_of_another_account__audit_not_called(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    other_account = create_test_account(name='Other')
    create_test_owner(
        account=other_account,
        email='other_owner@test.test',
    )
    target = create_test_not_admin(
        account=other_account,
        email='target@test.test',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    user_admin_toggled_mock = mocker.patch(
        'src.accounts.services.user.AuditEventService.user_admin_toggled',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(f'/accounts/users/{target.id}/toggle-admin')

    # assert
    assert response.status_code == 404
    target.refresh_from_db()
    assert target.is_admin is False
    user_admin_toggled_mock.assert_not_called()
    identify_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()
