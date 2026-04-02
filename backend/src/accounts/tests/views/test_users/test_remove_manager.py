"""Tests for POST /accounts/users/<id>/remove-manager."""

import pytest
from src.accounts.services.exceptions import UserServiceException
from src.accounts.services.user import UserService
from src.authentication.enums import AuthTokenType
from src.utils.validation import ErrorCode
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_remove_manager__ok(api_client, mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    manager = create_test_not_admin(
        account=account,
        email='manager@test.test',
    )
    team_member = create_test_not_admin(
        account=account,
        email='member@test.test',
    )
    team_member.manager = manager
    team_member.save()

    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
        return_value=team_member,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/accounts/users/{team_member.id}/remove-manager',
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=team_member,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        manager=None,
        force_save=True,
    )


def test_remove_manager__service_raise_exception__validation_error(
    api_client, mocker,
):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    team_member = create_test_not_admin(
        account=account,
        email='member@test.test',
    )
    error_message = 'Service error'
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
        side_effect=UserServiceException(message=error_message),
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/accounts/users/{team_member.id}/remove-manager',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == error_message
    user_service_init_mock.assert_called_once()
    partial_update_mock.assert_called_once()


def test_remove_manager__not_admin__permission_denied(api_client, mocker):
    # arrange
    account = create_test_account()
    not_admin = create_test_not_admin(account=account)
    team_member = create_test_not_admin(
        account=account,
        email='member@test.test',
    )
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )
    api_client.token_authenticate(not_admin)

    # act
    response = api_client.post(
        f'/accounts/users/{team_member.id}/remove-manager',
    )

    # assert
    assert response.status_code == 403
    partial_update_mock.assert_not_called()


def test_remove_manager__guest__permission_denied(api_client, mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(
        owner,
        tasks_count=1,
    )
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )
    team_member = create_test_not_admin(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )

    # act
    response = api_client.post(
        f'/accounts/users/{team_member.id}/remove-manager',
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 403
    partial_update_mock.assert_not_called()


def test_remove_manager__not_authenticated__unauthorized(api_client, mocker):
    # arrange
    account = create_test_account()
    team_member = create_test_not_admin(account=account)
    partial_update_mock = mocker.patch(
        'src.accounts.views.users.UserService.partial_update',
    )

    # act
    response = api_client.post(
        f'/accounts/users/{team_member.id}/remove-manager',
    )

    # assert
    assert response.status_code == 401
    partial_update_mock.assert_not_called()
