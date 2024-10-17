import pytest
import datetime
from django.utils import timezone
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_group,
    create_test_account,
    create_invited_user,
    create_test_guest,
)
from pneumatic_backend.accounts.messages import (
    MSG_A_0039,
)
from pneumatic_backend.accounts.services.group import UserGroupService
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
    UserStatus,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.services.exceptions import (
    UserGroupServiceException
)

pytestmark = pytest.mark.django_db


def test_update__ok(api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    another_user = create_test_user(
        account=account,
        email='another@pneumatic.app'
    )
    api_client.token_authenticate(user)
    group = create_test_group(user=user)
    request_data = {
        'name': 'Groups',
        'photo': 'https://foeih.com/image.jpg',
        'users': [another_user.id]
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    group_update = create_test_group(
        user=user,
        name=request_data['name'],
        photo=request_data['photo'],
        users=[another_user.id]
    )
    update_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.'
        'partial_update',
        return_value=group_update
    )

    # act
    response = api_client.put(
        path=f'/accounts/groups/{group.id}',
        data=request_data
    )

    # assert
    service_init_mock.assert_called_once_with(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    update_group_mock.assert_called_once_with(
        force_save=True,
        **request_data
    )
    assert response.status_code == 200
    data = response.data
    assert data['name'] == request_data['name']
    assert data['photo'] == request_data['photo']
    assert data['users'] == [another_user.id]


def test_update__yourself__ok(api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    group = create_test_group(user=user)
    request_data = {
        'name': 'Groups',
        'photo': 'https://foeih.com/image.jpg',
        'users': [user.id]
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    group_update = create_test_group(
        user=user,
        name=request_data['name'],
        photo=request_data['photo'],
        users=[user.id]
    )
    update_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.'
        'partial_update',
        return_value=group_update
    )

    # act
    response = api_client.put(
        path=f'/accounts/groups/{group.id}',
        data=request_data
    )

    # assert
    service_init_mock.assert_called_once_with(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    update_group_mock.assert_called_once_with(
        force_save=True,
        **request_data
    )
    assert response.status_code == 200
    data = response.data
    assert data['name'] == request_data['name']
    assert data['photo'] == request_data['photo']
    assert data['users'] == [user.id]


def test_update__not_admin__permission_denied(api_client, mocker):

    # arrange
    user = create_test_user()
    group = create_test_group(user=user, users=[user.id, ])
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    no_admin_user = create_test_user(
        account=account,
        email='no_admin@test.com',
        is_admin=False,
        is_account_owner=False
    )
    api_client.token_authenticate(no_admin_user)
    request_data = {
        'name': 'Group',
        'photo': 'https://foeih.com/image.jpg',
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    update_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create'
    )

    # act
    response = api_client.put(
        path=f'/accounts/groups/{group.id}',
        data=request_data
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    update_group_mock.assert_not_called()


def test_update__not_auth__permission_denied(api_client, mocker):

    # arrange
    user = create_test_user()
    group = create_test_group(user=user, users=[user.id, ])
    request_data = {
        'name': 'Group',
        'photo': 'https://foeih.com/image.jpg',
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    update_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create'
    )

    # act
    response = api_client.put(
        path=f'/accounts/groups/{group.id}',
        data=request_data
    )

    # assert
    assert response.status_code == 401
    service_init_mock.assert_not_called()
    update_group_mock.assert_not_called()


def test_update__expired_subscription__permission_denied(api_client, mocker):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - datetime.timedelta(hours=1)
    )
    user = create_test_user(account=account)
    group = create_test_group(user=user, users=[user.id, ])
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Group',
        'photo': 'https://foeih.com/image.jpg',
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    update_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create'
    )

    # act
    response = api_client.put(
        path=f'/accounts/groups/{group.id}',
        data=request_data
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    update_group_mock.assert_not_called()


def test_update__service_exception__validation_error(api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    another_user = create_test_user(email='another@pneumatic.app')
    api_client.token_authenticate(user)
    group = create_test_group(user=user, users=[user.id, another_user.id])
    request_data = {
        'name': 'Groups',
        'photo': 'https://foeih.com/image.jpg',
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    create_test_group(
        user=user,
        name=request_data['name'],
        photo=request_data['photo'],
        users=[user.id, another_user.id]
    )
    message = 'some message'
    update_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.'
        'partial_update',
        side_effect=UserGroupServiceException(message)
    )

    # act
    response = api_client.put(
        path=f'/accounts/groups/{group.id}',
        data=request_data
    )

    # assert
    service_init_mock.assert_called_once_with(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    update_group_mock.assert_called_once()
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message


def test_update__user_from_another_account__validation_error(
    api_client,
    mocker
):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    another_user = create_test_user(
        email='another@pneumatic.app'
    )
    api_client.token_authenticate(user)
    group = create_test_group(user=user)
    request_data = {
        'name': 'Groups',
        'photo': 'https://foeih.com/image.jpg',
        'users': [another_user.id]
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    update_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.'
        'partial_update',
    )

    # act
    response = api_client.put(
        path=f'/accounts/groups/{group.id}',
        data=request_data
    )

    # assert
    service_init_mock.assert_not_called()
    update_group_mock.assert_not_called()
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0039
    assert response.data['details']['reason'] == MSG_A_0039
    assert response.data['details']['name'] == 'users'


def test_update__invited_user__ok(api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    invited_user = create_invited_user(
        user=user,
        email='invited@pneumatic.app',
    )
    api_client.token_authenticate(user)
    group = create_test_group(user=user)
    request_data = {
        'name': 'Groups',
        'photo': 'https://foeih.com/image.jpg',
        'users': [invited_user.id]
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    group_update = create_test_group(
        user=user,
        name=request_data['name'],
        photo=request_data['photo'],
        users=[invited_user.id]
    )
    update_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.'
        'partial_update',
        return_value=group_update
    )

    # act
    response = api_client.put(
        path=f'/accounts/groups/{group.id}',
        data=request_data
    )

    # assert
    service_init_mock.assert_called_once_with(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    update_group_mock.assert_called_once_with(
        force_save=True,
        **request_data
    )
    assert response.status_code == 200
    data = response.data
    assert data['name'] == request_data['name']
    assert data['photo'] == request_data['photo']
    assert data['users'] == [invited_user.id]


def test_update__user_inactive__validation_error(api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    another_user = create_test_user(
        account=account,
        email='another@pneumatic.app',
        status=UserStatus.INACTIVE,
    )
    api_client.token_authenticate(user)
    group = create_test_group(user=user)
    request_data = {
        'name': 'Groups',
        'photo': 'https://foeih.com/image.jpg',
        'users': [another_user.id]
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    update_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.'
        'partial_update',
    )

    # act
    response = api_client.put(
        path=f'/accounts/groups/{group.id}',
        data=request_data
    )

    # assert
    service_init_mock.assert_not_called()
    update_group_mock.assert_not_called()
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0039
    assert response.data['details']['reason'] == MSG_A_0039
    assert response.data['details']['name'] == 'users'


def test_update__guest__validation_error(api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    guest_user = create_test_guest(
        account=account,
    )
    api_client.token_authenticate(user)
    group = create_test_group(user=user)
    request_data = {
        'name': 'Groups',
        'photo': 'https://foeih.com/image.jpg',
        'users': [guest_user.id]
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    update_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.'
        'partial_update',
    )

    # act
    response = api_client.put(
        path=f'/accounts/groups/{group.id}',
        data=request_data
    )

    # assert
    service_init_mock.assert_not_called()
    update_group_mock.assert_not_called()
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0039
    assert response.data['details']['reason'] == MSG_A_0039
    assert response.data['details']['name'] == 'users'


def test_update__fake_user_id__validation_error(api_client, mocker):
    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    group = create_test_group(user=user)
    request_data = {
        'name': 'Groups',
        'users': [2152]
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )

    update_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.'
        'partial_update'
    )

    # act
    response = api_client.put(
        path=f'/accounts/groups/{group.id}',
        data=request_data
    )

    # assert
    service_init_mock.assert_not_called()
    update_group_mock.assert_not_called()
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0039
    assert response.data['details']['reason'] == MSG_A_0039
    assert response.data['details']['name'] == 'users'
