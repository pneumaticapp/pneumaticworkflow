import pytest
from src.accounts.messages import MSG_A_0004
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.accounts.services.exceptions import (
    ReassignUserSameUser,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_user,
    create_test_guest,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_reassign__old_user_from_another_acc__validation_error(
    mocker,
    api_client,
):
    # arrange
    account_owner = create_test_user()
    user = create_invited_user(account_owner)
    another_account_user = create_test_user(
        email='newuser@pneumatic.app',
    )
    service_mock = mocker.patch(
        'src.accounts.views.users.'
        'ReassignService.reassign_everywhere',
    )
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': another_account_user.id,
            'new_user': user.id,
        },
    )

    # assert
    assert response.status_code == 400
    message = (
        f'Invalid pk "{another_account_user.id}" - object does not exist.'
    )
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'old_user'
    assert response.data['details']['reason'] == message
    service_mock.assert_not_called()


def test_reassign__new_user_from_another_acc__validation_error(
    mocker,
    api_client,
):
    # arrange
    account_owner = create_test_user()
    user = create_test_user(
        account=account_owner.account,
        email='new@pneumatic.app',
    )
    another_account_user = create_test_user(
        email='newuser@pneumatic.app',
    )
    api_client.token_authenticate(account_owner)
    service_mock = mocker.patch(
        'src.accounts.views.users.'
        'ReassignService.reassign_everywhere',
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': user.id,
            'new_user': another_account_user.id,
        },
    )

    # assert
    assert response.status_code == 400
    message = (
        f'Invalid pk "{another_account_user.id}" - object does not exist.'
    )
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'new_user'
    assert response.data['details']['reason'] == message
    service_mock.assert_not_called()


def test_reassign__with_valid_data__ok(mocker, api_client):
    # arrange
    account_owner = create_test_user()
    old_user = create_test_user(
        account=account_owner.account,
        email='new@pneumatic.app',
    )
    new_user = create_test_user(
        account=account_owner.account,
        email='new1@pneumatic.app',
    )
    api_client.token_authenticate(account_owner)
    service_class_mock = mocker.patch(
        'src.accounts.views.users.ReassignService',
    )
    service_instance_mock = service_class_mock.return_value

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        },
    )

    # assert
    assert response.status_code == 204
    service_class_mock.assert_called_once_with(
        is_superuser=False,
        auth_type='User',
        old_user=old_user,
        new_user=new_user,
    )
    service_instance_mock.reassign_everywhere.assert_called_once()


def test_reassign__invalid_field_type__validation_error(mocker, api_client):
    # arrange
    account_owner = create_test_user()
    new_user = create_test_user(
        account=account_owner.account,
        email='new@pneumatic.app',
    )
    api_client.token_authenticate(account_owner)
    service_class_mock = mocker.patch(
        'src.accounts.views.users.ReassignService',
    )
    service_instance_mock = service_class_mock.return_value

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': 'invalid-id',
            'new_user': new_user.id,
        },
    )

    # assert
    assert response.status_code == 400
    message = 'Incorrect type. Expected pk value, received str.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'old_user'
    assert response.data['details']['reason'] == message
    service_class_mock.assert_not_called()
    service_instance_mock.reassign_everywhere.assert_not_called()


def test_reassign__non_admin_user__permission_denied(mocker, api_client):
    # arrange
    account_owner = create_test_user()
    regular_user = create_test_user(
        account=account_owner.account,
        is_account_owner=False,
        is_admin=False,
        email='new@pneumatic.app',
    )
    old_user = create_test_user(
        account=account_owner.account,
        email='new1@pneumatic.app',
    )
    new_user = create_test_user(
        account=account_owner.account,
        email='new2@pneumatic.app',
    )
    api_client.token_authenticate(regular_user)
    service_class_mock = mocker.patch(
        'src.accounts.views.users.ReassignService',
    )
    service_instance_mock = service_class_mock.return_value

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        },
    )

    # assert
    assert response.status_code == 403
    service_class_mock.assert_not_called()
    service_instance_mock.reassign_everywhere.assert_not_called()


def test_reassign__guest__permission_denied(mocker, api_client):
    # arrange
    account_owner = create_test_user()
    guest = create_test_guest(account=account_owner.account)
    old_user = create_test_user(
        account=account_owner.account,
        email='new1@pneumatic.app',
    )
    new_user = create_test_user(
        account=account_owner.account,
        email='new2@pneumatic.app',
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account_owner.account.id,
    )
    service_class_mock = mocker.patch(
        'src.accounts.views.users.ReassignService',
    )
    service_instance_mock = service_class_mock.return_value

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        **{'X-Guest-Authorization': str_token},
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        },
    )

    # assert
    assert response.status_code == 403
    service_class_mock.assert_not_called()
    service_instance_mock.reassign_everywhere.assert_not_called()


def test_reassign__service_exception__returns_400(mocker, api_client):
    # arrange
    account_owner = create_test_user()
    old_user = create_invited_user(account_owner)
    new_user = create_invited_user(account_owner, email='new@pneumatic.app')
    api_client.token_authenticate(account_owner)
    service_class_mock = mocker.patch(
        'src.accounts.views.users.ReassignService',
    )
    service_instance = service_class_mock.return_value
    service_instance.reassign_everywhere.side_effect = (
        ReassignUserSameUser()
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0004
    service_class_mock.assert_called_once_with(
        is_superuser=False,
        auth_type='User',
        old_user=old_user,
        new_user=new_user,
    )
    service_instance.reassign_everywhere.assert_called_once()
