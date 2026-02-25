import pytest

from src.accounts.messages import MSG_A_0011
from src.accounts.services.exceptions import UserIsPerformerException
from src.accounts.services.user import UserService
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_user, create_test_owner, create_test_admin,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_delete_user__ok(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    request_user = create_test_user(account=account)
    deleted_user = create_test_user(
        account=account,
        email='deleted@test.test',
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    deactivate_mock = mocker.patch(
        'src.accounts.services.user.UserService.deactivate',
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.delete(
        f'/accounts/users/{deleted_user.id}',
    )

    # assert
    assert response.status_code == 204
    user_service_init_mock.assert_called_once_with(
        user=request_user,
        instance=deleted_user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    deactivate_mock.assert_called_once_with()


def test_delete__user_is_performer__validation_error(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    request_user = create_test_owner(account=account)
    deleted_user = create_test_admin(account=account)
    deactivate_mock = mocker.patch(
        'src.accounts.services.user.UserService.deactivate',
        side_effect=UserIsPerformerException(),
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.delete(f'/accounts/users/{deleted_user.id}')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0011
    deactivate_mock.assert_called_once_with()


def test_delete_user__another_account_user__not_found(
    mocker,
    api_client,
):
    # arrange
    request_user = create_test_user()
    another_user = create_test_user(email='another@test.test')
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    deactivate_mock = mocker.patch(
        'src.accounts.services.user.UserService.deactivate',
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.delete(
        f'/accounts/users/{another_user.id}',
    )

    # assert
    assert response.status_code == 404
    user_service_init_mock.assert_not_called()
    deactivate_mock.assert_not_called()


def test_delete_user__not_admin__permission_denied(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    create_test_user(account=account)
    request_user = create_test_user(
        account=account,
        is_admin=False,
        is_account_owner=False,
        email='test@test.test',
    )
    deleted_user = create_test_user(
        email='deleted@test.test',
        account=account,
    )
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    deactivate_mock = mocker.patch(
        'src.accounts.services.user.UserService'
        '.deactivate',
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.delete(
        f'/accounts/users/{deleted_user.id}',
    )

    # assert
    assert response.status_code == 403
    deactivate_mock.assert_not_called()
    user_service_init_mock.assert_not_called()
