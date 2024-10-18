import datetime
from django.utils import timezone
import pytest
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
    LeaseLevel,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
)


pytestmark = pytest.mark.django_db


def test_token__partner__ok(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_account_owner = create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    token_data = {
        'token': 'some token'
    }
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.services.AuthService'
        '.get_auth_token',
        return_value=token_data
    )
    tenants_accessed_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'tenants_accessed'
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.get(f'/tenants/{tenant_account.id}/token')

    # assert
    assert response.data['token']
    assert response.status_code == 200
    tenants_accessed_mock.assert_called_once_with(
        master_user=master_account_owner,
        tenant_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    authenticate_mock.assert_called_once_with(
        user=tenant_account_owner,
        user_agent='Firefox',
        user_ip='192.168.0.1',
        superuser_mode=True,
    )


@pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
def test_token__any_premium_plan__ok(
    plan,
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=plan,
        lease_level=LeaseLevel.STANDARD
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        plan=plan,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_account_owner = create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    api_client.token_authenticate(master_account_owner)
    token_data = {
        'token': 'some token'
    }
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.services.AuthService'
        '.get_auth_token',
        return_value=token_data
    )
    tenants_accessed_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'tenants_accessed'
    )

    # act
    response = api_client.get(f'/tenants/{tenant_account.id}/token')

    # assert
    assert response.data['token']
    assert response.status_code == 200
    tenants_accessed_mock.assert_called_once_with(
        master_user=master_account_owner,
        tenant_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    authenticate_mock.assert_called_once_with(
        user=tenant_account_owner,
        user_agent='Firefox',
        user_ip='192.168.0.1',
        superuser_mode=True,
    )


def test_token__tenant__permission_denied(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT
    )
    account_owner = create_test_user(account=account)
    tenant_account = create_test_account(
        name='tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=account
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    api_client.token_authenticate(account_owner)
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.services.AuthService'
        '.get_auth_token',
    )
    tenants_accessed_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'tenants_accessed'
    )

    # act
    response = api_client.get(f'/tenants/{tenant_account.id}/token')

    # assert
    assert response.status_code == 403
    authenticate_mock.assert_not_called()
    tenants_accessed_mock.assert_not_called()


def test_token__free_plan__permission_denied(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account(plan=BillingPlanType.FREEMIUM)
    account_owner = create_test_user(account=account)
    tenant_account = create_test_account(
        name='tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=account
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    api_client.token_authenticate(account_owner)
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.services.AuthService'
        '.get_auth_token',
    )

    # act
    response = api_client.get(f'/tenants/{tenant_account.id}/token')

    # assert
    assert response.status_code == 403
    authenticate_mock.assert_not_called()


def test_token__expired_subscription__permission_denied(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - datetime.timedelta(hours=1)
    )
    account_owner = create_test_user(account=account)
    tenant_account = create_test_account(
        name='tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=account
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    api_client.token_authenticate(account_owner)
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.services.AuthService'
        '.get_auth_token',
    )

    # act
    response = api_client.get(f'/tenants/{tenant_account.id}/token')

    # assert
    assert response.status_code == 403
    authenticate_mock.assert_not_called()


def test_token__another_account_tenant__permission_denied(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.STANDARD
    )
    account_owner = create_test_user(account=account)
    another_account = create_test_account(
        name='another account',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.STANDARD
    )
    create_test_user(
        account=another_account,
        email='another_owner@test.test'
    )
    another_tenant_account = create_test_account(
        name='tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=another_account
    )
    create_test_user(
        account=another_tenant_account,
        email='tenant_owner@test.test'
    )
    api_client.token_authenticate(account_owner)
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.services.AuthService'
        '.get_auth_token',
    )

    # act
    response = api_client.get(
        f'/tenants/{another_tenant_account.id}/token'
    )

    # assert
    assert response.status_code == 403
    authenticate_mock.assert_not_called()


def test_token__not_admin__permission_denied(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
    )
    master_account_not_admin = create_test_user(
        account=master_account,
        is_admin=False,
        is_account_owner=False
    )
    tenant_account = create_test_account(
        name='tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.services.AuthService'
        '.get_auth_token',
    )
    api_client.token_authenticate(master_account_not_admin)

    # act
    response = api_client.get(f'/tenants/{tenant_account.id}/token')

    # assert
    assert response.status_code == 403
    authenticate_mock.assert_not_called()


@pytest.mark.parametrize('lease_level', LeaseLevel.NOT_TENANT_LEVELS)
def test_token__not_tenant__permission_denied(
    mocker,
    api_client,
    lease_level,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        lease_level=lease_level
    )
    master_account_not_admin = create_test_user(
        account=master_account,
        is_admin=False,
        is_account_owner=False
    )
    another_tenant_account = create_test_account(
        name='tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
    )
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.services.AuthService'
        '.get_auth_token',
    )
    api_client.token_authenticate(master_account_not_admin)

    # act
    response = api_client.get(
        f'/tenants/{another_tenant_account.id}/token'
    )

    # assert
    assert response.status_code == 403
    authenticate_mock.assert_not_called()


def test_list__not_authenticated__auth_error(
    api_client,
):
    tenant_account = create_test_account(
        name='tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
    )

    # act
    response = api_client.get(f'/tenants/{tenant_account.id}/token')

    # assert
    assert response.status_code == 401
