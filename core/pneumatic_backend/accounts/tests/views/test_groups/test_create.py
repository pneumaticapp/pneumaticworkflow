import pytest
import datetime
from django.utils import timezone
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.accounts.services.group import UserGroupService
from pneumatic_backend.accounts.messages import (
    MSG_A_0024,
    MSG_A_0039,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_group,
    create_test_account,
    create_invited_user,
    create_test_guest
)
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
    UserStatus,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.services.exceptions import (
    UserGroupServiceException
)

pytestmark = pytest.mark.django_db


def test_create__all_fields__ok(api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    another_user = create_test_user(
        email='another@pneumatic.app',
        account=account
    )
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Group',
        'photo': 'https://foeih.com/image.jpg',
        'users': [user.id, another_user.id],
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    group = create_test_group(user=user, users=request_data['users'])
    create_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create',
        return_value=group
    )

    # act
    response = api_client.post(
        path='/accounts/groups',
        data=request_data
    )

    # assert
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    create_group_mock.assert_called_once_with(
        **request_data
    )
    assert response.status_code == 200
    data = response.data
    assert data['name'] == request_data['name']
    assert data['photo'] == request_data['photo']
    assert data['users'] == request_data['users']


def test_create__required_fields__ok(api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    create_test_user(
        email='another@pneumatic.app',
        account=account
    )
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Group',
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    group = create_test_group(user=user)
    create_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create',
        return_value=group
    )

    # act
    response = api_client.post(
        path='/accounts/groups',
        data=request_data
    )

    # assert
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    create_group_mock.assert_called_once_with(
        **request_data
    )
    assert response.status_code == 200
    data = response.data
    assert data['name'] == request_data['name']
    assert 'photo' not in data
    assert 'users' not in data


def test_create__user_from_another_account__validation_error(
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
    request_data = {
        'name': 'Group',
        'users': [user.id, another_user.id],
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    create_test_group(user=user, users=request_data['users'])
    create_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create'
    )

    # act
    response = api_client.post(
        path='/accounts/groups',
        data=request_data
    )

    # assert
    service_init_mock.assert_not_called()
    create_group_mock.assert_not_called()
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0039
    assert response.data['details']['reason'] == MSG_A_0039
    assert response.data['details']['name'] == 'users'


def test_create__fake_user_id__validation_error(api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Group',
        'photo': 'https://foeih.com/image.jpg',
        'users': [3216],
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    create_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create'
    )

    # act
    response = api_client.post(
        path='/accounts/groups',
        data=request_data
    )

    # assert
    service_init_mock.assert_not_called()
    create_group_mock.assert_not_called()
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0039
    assert response.data['details']['reason'] == MSG_A_0039
    assert response.data['details']['name'] == 'users'


def test_create__invited_user__ok(api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    invited_user = create_invited_user(
        user=user,
        email='invited@pneumatic.app',
    )
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Group',
        'users': [invited_user.id],
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    group = create_test_group(user=user, users=request_data['users'])
    create_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create',
        return_value=group
    )

    # act
    response = api_client.post(
        path='/accounts/groups',
        data=request_data
    )

    # assert
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    create_group_mock.assert_called_once_with(
        **request_data
    )
    assert response.status_code == 200
    data = response.data
    assert data['name'] == request_data['name']
    assert data['users'] == request_data['users']


def test_create__user_inactive__validation_error(api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    another_user = create_test_user(
        email='another@pneumatic.app',
        account=account,
        status=UserStatus.INACTIVE,
    )
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Group',
        'users': [another_user.id],
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    create_test_group(user=user, users=request_data['users'])
    create_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create'
    )

    # act
    response = api_client.post(
        path='/accounts/groups',
        data=request_data
    )

    # assert
    service_init_mock.assert_not_called()
    create_group_mock.assert_not_called()
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0039
    assert response.data['details']['reason'] == MSG_A_0039
    assert response.data['details']['name'] == 'users'


def test_create__guest__validation_error(api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    guest_user = create_test_guest(
        account=account,
    )
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Group',
        'users': [guest_user.id],
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    create_test_group(user=user, users=request_data['users'])
    create_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create'
    )

    # act
    response = api_client.post(
        path='/accounts/groups',
        data=request_data
    )

    # assert
    service_init_mock.assert_not_called()
    create_group_mock.assert_not_called()
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0039
    assert response.data['details']['reason'] == MSG_A_0039
    assert response.data['details']['name'] == 'users'


def test_create__not_name__validation_error(api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    request_data = {
        'photo': 'https://foeih.com/image.jpg',
        'users': [user.id, ],
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    create_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create'
    )

    # act
    response = api_client.post(
        path='/accounts/groups',
        data=request_data
    )

    # assert
    service_init_mock.assert_not_called()
    create_group_mock.assert_not_called()
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0024
    assert response.data['details']['reason'] == MSG_A_0024
    assert response.data['details']['name'] == 'name'


def test_create__users_empty_list__ok(api_client, mocker):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Group',
        'users': [],
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    group = create_test_group(user=user, users=request_data['users'])
    create_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create',
        return_value=group
    )

    # act
    response = api_client.post(
        path='/accounts/groups',
        data=request_data
    )

    # assert
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    create_group_mock.assert_called_once_with(
        **request_data
    )
    assert response.status_code == 200
    data = response.data
    assert data['users'] == request_data['users']


def test_create__invalid_list_users__validation_error(
    api_client,
    mocker
):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Group',
        'users': 'invalid_list',
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    create_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create'
    )

    # act
    response = api_client.post(
        path='/accounts/groups',
        data=request_data
    )

    # assert
    service_init_mock.assert_not_called()
    create_group_mock.assert_not_called()
    assert response.status_code == 400
    message = 'Expected a list of items but got type "str".'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'users'


def test_create__not_admin__permission_denied(api_client, mocker):
    # arrange
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
        'users': [no_admin_user.id, ],
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    create_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create'
    )

    # act
    response = api_client.post(
        path='/accounts/groups',
        data=request_data
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    create_group_mock.assert_not_called()


def test_create__not_auth__permission_denied(api_client, mocker):
    # arrange
    user = create_test_user()
    request_data = {
        'name': 'Group',
        'users': [user.id, ],
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    create_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create'
    )

    # act
    response = api_client.post(
        path='/accounts/groups',
        data=request_data
    )

    # assert
    assert response.status_code == 401
    service_init_mock.assert_not_called()
    create_group_mock.assert_not_called()


def test_create__expired_subscription__permission_denied(api_client, mocker):
    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - datetime.timedelta(hours=1)
    )
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Group',
        'users': [user.id, ],
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    create_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create'
    )

    # act
    response = api_client.post(
        path='/accounts/groups',
        data=request_data
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    create_group_mock.assert_not_called()


def test_create__service_exception__validation_error(api_client, mocker):
    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    request_data = {
        'name': 'Group',
        'users': [user.id, ],
    }
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None
    )
    message = 'some message'
    create_group_mock = mocker.patch(
        'pneumatic_backend.accounts.services.group.UserGroupService.create',
        side_effect=UserGroupServiceException(message)
    )

    # act
    response = api_client.post(
        path='/accounts/groups',
        data=request_data
    )

    # assert
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    create_group_mock.assert_called_once()
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
