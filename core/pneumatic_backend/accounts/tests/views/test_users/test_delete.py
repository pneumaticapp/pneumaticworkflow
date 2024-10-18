import pytest
from pneumatic_backend.accounts.tests.fixtures import (
    create_test_user,
    create_test_account
)
from pneumatic_backend.accounts.services.exceptions import (
    UserIsPerformerException,
)
from pneumatic_backend.accounts.messages import (
    MSG_A_0011,
)
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


def test_delete_user__ok(
    mocker,
    api_client
):
    # arrange
    account = create_test_account()
    request_user = create_test_user(account=account)
    deleted_user = create_test_user(
        account=account,
        email='deleted@test.test'
    )
    deactivate_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService'
        '.deactivate'
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.post(
        f'/accounts/users/{deleted_user.id}/delete'
    )

    # assert
    assert response.status_code == 204
    deactivate_mock.assert_called_once_with(deleted_user)


def test_delete__user_is_performer__validation_error(
    mocker,
    api_client
):
    # arrange
    account = create_test_account()
    request_user = create_test_user(account=account)
    deleted_user = create_test_user(
        account=account,
        email='deleted@test.test'
    )
    deactivate_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService'
        '.deactivate',
        side_effect=UserIsPerformerException()
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.post(f'/accounts/users/{deleted_user.id}/delete')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0011
    deactivate_mock.assert_called_once_with(deleted_user)


def test_delete_user__another_account_user__not_found(
    mocker,
    api_client
):
    # arrange
    request_user = create_test_user()
    another_user = create_test_user(email='another@test.test')
    deactivate_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService'
        '.deactivate'
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.post(
        f'/accounts/users/{another_user.id}/delete'
    )

    # assert
    assert response.status_code == 404
    deactivate_mock.assert_not_called()


def test_delete_user__not_admin__permission_denied(
    mocker,
    api_client
):
    # arrange
    account = create_test_account()
    request_user = create_test_user(is_admin=False)
    deleted_user = create_test_user(
        email='deleted@test.test',
        account=account
    )
    deactivate_mock = mocker.patch(
        'pneumatic_backend.accounts.services.user.UserService'
        '.deactivate'
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.post(
        f'/accounts/users/{deleted_user.id}/delete'
    )

    # assert
    assert response.status_code == 403
    deactivate_mock.assert_not_called()
