import pytest
import datetime
from django.utils import timezone
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_group,
    create_test_account,
)
from src.accounts.enums import (
    BillingPlanType,
)
from src.accounts.services.group import UserGroupService
from src.authentication.enums import AuthTokenType

pytestmark = pytest.mark.django_db


def test_groups_delete_group_ok(api_client, mocker):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    group = create_test_group(account, users=[user])
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None,
    )
    service_delete_mock = mocker.patch(
        'src.accounts.services.group.'
        'UserGroupService.delete',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.delete(
        path=f'/accounts/groups/{group.id}',
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        user=user,
        instance=group,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    service_delete_mock.assert_called_once()


@pytest.mark.parametrize(
    'plan', (BillingPlanType.FREEMIUM, BillingPlanType.PREMIUM))
def test_delete__group_owner_removed_from_workflow_in_all_plan__ok(
    api_client, plan, mocker,
):
    # Arrange
    account = create_test_account(plan=plan)
    user = create_test_user(account=account)
    group_to_delete = create_test_group(account, users=[user])
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None,
    )
    service_delete_mock = mocker.patch(
        'src.accounts.services.group.'
        'UserGroupService.delete',
    )
    api_client.token_authenticate(user)

    # Act
    response = api_client.delete(
        path=f'/accounts/groups/{group_to_delete.id}',
    )

    # Assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        user=user,
        instance=group_to_delete,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    service_delete_mock.assert_called_once()


def test_delete__not_admin__permission_denied(api_client, mocker):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    group_to_delete = create_test_group(account, users=[user])
    no_admin_user = create_test_user(
        account=account,
        email='no_admin@test.com',
        is_admin=False,
        is_account_owner=False,
    )
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None,
    )
    service_delete_mock = mocker.patch(
        'src.accounts.services.group.'
        'UserGroupService.delete',
    )
    api_client.token_authenticate(no_admin_user)

    # act
    response = api_client.delete(
        path=f'/accounts/groups/{group_to_delete.id}',
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    service_delete_mock.assert_not_called()


def test_delete__not_auth__permission_denied(api_client, mocker):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    group = create_test_group(account, users=[user])
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None,
    )
    service_delete_mock = mocker.patch(
        'src.accounts.services.group.'
        'UserGroupService.delete',
    )

    # act
    response = api_client.delete(
        path=f'/accounts/groups/{group.id}',
    )

    # assert
    assert response.status_code == 401
    service_init_mock.assert_not_called()
    service_delete_mock.assert_not_called()


def test_delete__expired_subscription__permission_denied(api_client, mocker):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - datetime.timedelta(hours=1),
    )
    user = create_test_user(account=account)
    group = create_test_group(account, users=[user])
    service_init_mock = mocker.patch.object(
        UserGroupService,
        attribute='__init__',
        return_value=None,
    )
    service_delete_mock = mocker.patch(
        'src.accounts.services.group.'
        'UserGroupService.delete',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.delete(
        path=f'/accounts/groups/{group.id}',
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    service_delete_mock.assert_not_called()
