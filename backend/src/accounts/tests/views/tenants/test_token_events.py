import pytest

from src.accounts.enums import (
    BillingPlanType,
    LeaseLevel,
)
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_token__master_account__audit_tenant_logged_in_as(
    mocker,
    api_client,
):

    # arrange
    master_account = create_test_account()
    master_account_owner = create_test_owner(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
    )
    tenant_account_owner = create_test_owner(
        account=tenant_account,
        email='tenant_owner@test.test',
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService'
        '.get_auth_token',
        return_value='some token',
    )
    tenants_accessed_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'tenants_accessed',
    )
    tenant_logged_in_as_mock = mocker.patch(
        'src.authentication.services.user_auth.AuditEventService.'
        'tenant_logged_in_as',
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.get(f'/tenants/{tenant_account.id}/token')

    # assert
    assert response.status_code == 200
    tenant_logged_in_as_mock.assert_called_once_with(
        user=master_account_owner,
        auth_type=AuthTokenType.USER,
        tenant_account=tenant_account,
    )
    get_auth_token_mock.assert_called_once_with(
        user=tenant_account_owner,
        user_agent='Firefox',
        user_ip='192.168.0.1',
        superuser_mode=True,
    )
    tenants_accessed_mock.assert_called_once_with(
        master_user=master_account_owner,
        tenant_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_token__not_own_tenant__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account(lease_level=LeaseLevel.STANDARD)
    account_owner = create_test_owner(account=account)
    another_account = create_test_account(
        name='another account',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.STANDARD,
    )
    another_tenant_account = create_test_account(
        name='tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=another_account,
    )
    create_test_owner(
        account=another_tenant_account,
        email='tenant_owner@test.test',
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService'
        '.get_auth_token',
    )
    tenant_logged_in_as_mock = mocker.patch(
        'src.authentication.services.user_auth.AuditEventService.'
        'tenant_logged_in_as',
    )
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get(
        f'/tenants/{another_tenant_account.id}/token',
    )

    # assert
    assert response.status_code == 403
    tenant_logged_in_as_mock.assert_not_called()
    get_auth_token_mock.assert_not_called()
