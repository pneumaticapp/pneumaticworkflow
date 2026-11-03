import pytest

from src.accounts.messages import MSG_A_0004
from src.accounts.services.exceptions import ReassignUserSameUser
from src.accounts.services.reassign import ReassignService
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_reassign__user_to_user__audit_user_reassigned(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    old_user = create_test_not_admin(
        account=account,
        email='old@test.test',
    )
    new_user = create_test_not_admin(
        account=account,
        email='new@test.test',
    )
    reassign_service_init_mock = mocker.patch.object(
        ReassignService,
        attribute='__init__',
        return_value=None,
    )
    reassign_everywhere_mock = mocker.patch.object(
        ReassignService,
        attribute='reassign_everywhere',
    )
    user_reassigned_mock = mocker.patch(
        'src.accounts.views.users.AuditEventService.user_reassigned',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={'old_user': old_user.id, 'new_user': new_user.id},
        format='json',
    )

    # assert
    assert response.status_code == 204
    user_reassigned_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        old_user=old_user,
        new_user=new_user,
    )
    reassign_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        request_user=owner,
        old_user=old_user,
        new_user=new_user,
    )
    reassign_everywhere_mock.assert_called_once_with()


def test_reassign__group_to_group__audit_user_reassigned(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    old_group = create_test_group(
        account=account,
        name='old',
    )
    new_group = create_test_group(
        account=account,
        name='new',
    )
    reassign_service_init_mock = mocker.patch.object(
        ReassignService,
        attribute='__init__',
        return_value=None,
    )
    reassign_everywhere_mock = mocker.patch.object(
        ReassignService,
        attribute='reassign_everywhere',
    )
    user_reassigned_mock = mocker.patch(
        'src.accounts.views.users.AuditEventService.user_reassigned',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={'old_group': old_group.id, 'new_group': new_group.id},
        format='json',
    )

    # assert
    assert response.status_code == 204
    user_reassigned_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        old_group=old_group,
        new_group=new_group,
    )
    reassign_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        request_user=owner,
        old_group=old_group,
        new_group=new_group,
    )
    reassign_everywhere_mock.assert_called_once_with()


def test_reassign__user_to_group__audit_user_reassigned(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    old_user = create_test_not_admin(account=account)
    new_group = create_test_group(account=account)
    reassign_service_init_mock = mocker.patch.object(
        ReassignService,
        attribute='__init__',
        return_value=None,
    )
    reassign_everywhere_mock = mocker.patch.object(
        ReassignService,
        attribute='reassign_everywhere',
    )
    user_reassigned_mock = mocker.patch(
        'src.accounts.views.users.AuditEventService.user_reassigned',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={'old_user': old_user.id, 'new_group': new_group.id},
        format='json',
    )

    # assert
    assert response.status_code == 204
    user_reassigned_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        old_user=old_user,
        new_group=new_group,
    )
    reassign_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        request_user=owner,
        old_user=old_user,
        new_group=new_group,
    )
    reassign_everywhere_mock.assert_called_once_with()


def test_reassign__service_exception__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    old_user = create_test_not_admin(
        account=account,
        email='old@test.test',
    )
    new_user = create_test_not_admin(
        account=account,
        email='new@test.test',
    )
    reassign_service_init_mock = mocker.patch.object(
        ReassignService,
        attribute='__init__',
        return_value=None,
    )
    reassign_everywhere_mock = mocker.patch.object(
        ReassignService,
        attribute='reassign_everywhere',
        side_effect=ReassignUserSameUser(),
    )
    user_reassigned_mock = mocker.patch(
        'src.accounts.views.users.AuditEventService.user_reassigned',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={'old_user': old_user.id, 'new_user': new_user.id},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0004
    assert response.data['details'] == {}
    user_reassigned_mock.assert_not_called()
    reassign_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        request_user=owner,
        old_user=old_user,
        new_user=new_user,
    )
    reassign_everywhere_mock.assert_called_once_with()


def test_reassign__invalid_old_user__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    new_user = create_test_not_admin(account=account)
    reassign_service_init_mock = mocker.patch.object(
        ReassignService,
        attribute='__init__',
        return_value=None,
    )
    reassign_everywhere_mock = mocker.patch.object(
        ReassignService,
        attribute='reassign_everywhere',
    )
    user_reassigned_mock = mocker.patch(
        'src.accounts.views.users.AuditEventService.user_reassigned',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={'old_user': 'invalid-id', 'new_user': new_user.id},
        format='json',
    )

    # assert
    message = 'Incorrect type. Expected pk value, received str.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'old_user'
    assert response.data['details']['reason'] == message
    user_reassigned_mock.assert_not_called()
    reassign_service_init_mock.assert_not_called()
    reassign_everywhere_mock.assert_not_called()
