import pytest

from src.authentication.services.guest_auth import GuestJWTAuthService
from src.permissions.enums import PermissionObjectType
from src.permissions.services import UserObjectPermissionService
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_owner,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_permission__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_object_permission_service_init_mock = mocker.patch.object(
        UserObjectPermissionService,
        attribute='__init__',
        return_value=None,
    )
    get_permissions_mock = mocker.patch(
        'src.permissions.services.'
        'UserObjectPermissionService.get_permissions',
        return_value=[
            {'id': 1, 'has_view': True, 'has_change': False},
            {'id': 2, 'has_view': False, 'has_change': False},
        ],
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        '/accounts/user/permission',
        data={
            'obj_type': PermissionObjectType.WORKFLOW,
            'obj_ids': '1,2',
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == 1
    assert response.data[0]['has_view'] is True
    assert response.data[0]['has_change'] is False
    assert response.data[1]['id'] == 2
    assert response.data[1]['has_view'] is False
    assert response.data[1]['has_change'] is False
    user_object_permission_service_init_mock.assert_called_once_with(
        user=owner,
    )
    get_permissions_mock.assert_called_once_with(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[1, 2],
    )


def test_permission__duplicate_ids__passed_as_is(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_object_permission_service_init_mock = mocker.patch.object(
        UserObjectPermissionService,
        attribute='__init__',
        return_value=None,
    )
    get_permissions_mock = mocker.patch(
        'src.permissions.services.'
        'UserObjectPermissionService.get_permissions',
        return_value=[
            {'id': 1, 'has_view': True, 'has_change': True},
        ],
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        '/accounts/user/permission',
        data={
            'obj_type': PermissionObjectType.WORKFLOW,
            'obj_ids': '1,1',
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == 1
    user_object_permission_service_init_mock.assert_called_once_with(
        user=owner,
    )
    get_permissions_mock.assert_called_once_with(
        obj_type=PermissionObjectType.WORKFLOW,
        obj_ids=[1, 1],
    )


def test_permission__real_workflow__ok(api_client):

    """Single end-to-end case without mocks. The permission matrix
    is covered by the UserObjectPermissionService tests."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        '/accounts/user/permission',
        data={
            'obj_type': PermissionObjectType.WORKFLOW,
            'obj_ids': f'{workflow.id},999999',
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == workflow.id
    assert response.data[0]['has_view'] is True
    assert response.data[0]['has_change'] is True
    assert response.data[1]['id'] == 999999
    assert response.data[1]['has_view'] is False
    assert response.data[1]['has_change'] is False


def test_permission__invalid_obj_type__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    get_permissions_mock = mocker.patch(
        'src.permissions.services.'
        'UserObjectPermissionService.get_permissions',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        '/accounts/user/permission',
        data={
            'obj_type': 'template',
            'obj_ids': '1',
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    message = '"template" is not a valid choice.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'obj_type'
    assert response.data['details']['reason'] == message
    get_permissions_mock.assert_not_called()


def test_permission__obj_type_blank__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    get_permissions_mock = mocker.patch(
        'src.permissions.services.'
        'UserObjectPermissionService.get_permissions',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        '/accounts/user/permission',
        data={
            'obj_type': '',
            'obj_ids': '1',
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    message = '"" is not a valid choice.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'obj_type'
    assert response.data['details']['reason'] == message
    get_permissions_mock.assert_not_called()


def test_permission__obj_type_undefined__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    get_permissions_mock = mocker.patch(
        'src.permissions.services.'
        'UserObjectPermissionService.get_permissions',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        '/accounts/user/permission',
        data={
            'obj_type': 'undefined',
            'obj_ids': '1',
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    message = '"undefined" is not a valid choice.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'obj_type'
    assert response.data['details']['reason'] == message
    get_permissions_mock.assert_not_called()


def test_permission__obj_type_missing__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    get_permissions_mock = mocker.patch(
        'src.permissions.services.'
        'UserObjectPermissionService.get_permissions',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        '/accounts/user/permission',
        data={'obj_ids': '1'},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    message = 'This field is required.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'obj_type'
    assert response.data['details']['reason'] == message
    get_permissions_mock.assert_not_called()


def test_permission__obj_ids_missing__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    get_permissions_mock = mocker.patch(
        'src.permissions.services.'
        'UserObjectPermissionService.get_permissions',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        '/accounts/user/permission',
        data={'obj_type': PermissionObjectType.WORKFLOW},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    message = 'This field is required.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'obj_ids'
    assert response.data['details']['reason'] == message
    get_permissions_mock.assert_not_called()


def test_permission__obj_ids_blank__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    get_permissions_mock = mocker.patch(
        'src.permissions.services.'
        'UserObjectPermissionService.get_permissions',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        '/accounts/user/permission',
        data={
            'obj_type': PermissionObjectType.WORKFLOW,
            'obj_ids': '',
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    message = 'This field is required.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'obj_ids'
    assert response.data['details']['reason'] == message
    get_permissions_mock.assert_not_called()


def test_permission__obj_ids_undefined__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    get_permissions_mock = mocker.patch(
        'src.permissions.services.'
        'UserObjectPermissionService.get_permissions',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        '/accounts/user/permission',
        data={
            'obj_type': PermissionObjectType.WORKFLOW,
            'obj_ids': 'undefined',
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    message = 'A valid integer is required.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'obj_ids'
    assert response.data['details']['reason'] == message
    get_permissions_mock.assert_not_called()


def test_permission__obj_ids_not_integer__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    get_permissions_mock = mocker.patch(
        'src.permissions.services.'
        'UserObjectPermissionService.get_permissions',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        '/accounts/user/permission',
        data={
            'obj_type': PermissionObjectType.WORKFLOW,
            'obj_ids': '1,abc',
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    message = 'A valid integer is required.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'obj_ids'
    assert response.data['details']['reason'] == message
    get_permissions_mock.assert_not_called()


def test_permission__obj_ids_empty_item__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    get_permissions_mock = mocker.patch(
        'src.permissions.services.'
        'UserObjectPermissionService.get_permissions',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        '/accounts/user/permission',
        data={
            'obj_type': PermissionObjectType.WORKFLOW,
            'obj_ids': '1,,2',
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    message = 'A valid integer is required.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'obj_ids'
    assert response.data['details']['reason'] == message
    get_permissions_mock.assert_not_called()


def test_permission__obj_ids_zero__validation_error(
    api_client,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    get_permissions_mock = mocker.patch(
        'src.permissions.services.'
        'UserObjectPermissionService.get_permissions',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        '/accounts/user/permission',
        data={
            'obj_type': PermissionObjectType.WORKFLOW,
            'obj_ids': '0',
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    message = 'Ensure this value is greater than or equal to 1.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'obj_ids'
    assert response.data['details']['reason'] == message
    get_permissions_mock.assert_not_called()


def test_permission__not_authenticated__unauthorized(api_client, mocker):

    # arrange
    get_permissions_mock = mocker.patch(
        'src.permissions.services.'
        'UserObjectPermissionService.get_permissions',
    )

    # act
    response = api_client.get(
        '/accounts/user/permission',
        data={
            'obj_type': PermissionObjectType.WORKFLOW,
            'obj_ids': '1',
        },
    )

    # assert
    assert response.status_code == 401
    get_permissions_mock.assert_not_called()


def test_permission__guest__permission_denied(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )
    get_permissions_mock = mocker.patch(
        'src.permissions.services.'
        'UserObjectPermissionService.get_permissions',
    )

    # act
    response = api_client.get(
        '/accounts/user/permission',
        data={
            'obj_type': PermissionObjectType.WORKFLOW,
            'obj_ids': str(workflow.id),
        },
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 403
    get_permissions_mock.assert_not_called()
