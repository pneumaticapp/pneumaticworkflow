import pytest

from src.accounts.enums import BillingPlanType, LeaseLevel
from src.accounts.models import Account
from src.accounts.services.account import AccountService
from src.authentication.enums import AuthTokenType
from src.payment.messages import MSG_BL_0005
from src.payment.stripe.exceptions import SubscriptionNotExist
from src.payment.stripe.service import StripeService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_delete__free_plan__audit_tenant_deleted(
    mocker,
    api_client,
):

    # arrange
    master_account = create_test_account()
    master_owner = create_test_owner(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='Tenant name',
        plan=BillingPlanType.FREEMIUM,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
    )
    create_test_owner(
        account=tenant_account,
        email='tenant_owner@test.test',
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None,
    )
    update_users_counts_mock = mocker.patch(
        'src.accounts.services.account.AccountService.update_users_counts',
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    increase_plan_users_mock = mocker.patch(
        'src.accounts.views.tenants.increase_plan_users.delay',
    )
    tenant_deleted_mock = mocker.patch(
        'src.accounts.views.tenants.AuditEventService.tenant_deleted',
    )
    api_client.token_authenticate(master_owner)

    # act
    response = api_client.delete(f'/tenants/{tenant_account.id}')

    # assert
    assert response.status_code == 204
    assert not Account.objects.filter(id=tenant_account.id).exists()
    tenant_deleted_mock.assert_called_once_with(
        user=master_owner,
        auth_type=AuthTokenType.USER,
        tenant=tenant_account,
    )
    account_service_init_mock.assert_called_once_with(
        instance=master_account,
        user=master_owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    update_users_counts_mock.assert_called_once_with()
    stripe_service_init_mock.assert_not_called()
    increase_plan_users_mock.assert_not_called()


def test_delete__stripe_exception__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    master_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    master_owner = create_test_owner(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='Tenant name',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
    )
    create_test_owner(
        account=tenant_account,
        email='tenant_owner@test.test',
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None,
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    cancel_subscription_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.cancel_subscription',
        side_effect=SubscriptionNotExist(),
    )
    increase_plan_users_mock = mocker.patch(
        'src.accounts.views.tenants.increase_plan_users.delay',
    )
    tenant_deleted_mock = mocker.patch(
        'src.accounts.views.tenants.AuditEventService.tenant_deleted',
    )
    api_client.token_authenticate(master_owner)

    # act
    response = api_client.delete(f'/tenants/{tenant_account.id}')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_BL_0005
    assert response.data['details'] == {}
    assert Account.objects.filter(id=tenant_account.id).exists()
    tenant_deleted_mock.assert_not_called()
    stripe_service_init_mock.assert_called_once_with(
        user=master_owner,
        subscription_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    cancel_subscription_mock.assert_called_once_with()
    account_service_init_mock.assert_not_called()
    increase_plan_users_mock.assert_not_called()


def test_delete__another_account_tenant__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    master_account = create_test_account()
    master_owner = create_test_owner(account=master_account)
    another_tenant = create_test_account(
        name='tenant',
        tenant_name='Tenant name',
        lease_level=LeaseLevel.TENANT,
    )
    create_test_owner(
        account=another_tenant,
        email='tenant_owner@test.test',
    )
    increase_plan_users_mock = mocker.patch(
        'src.accounts.views.tenants.increase_plan_users.delay',
    )
    tenant_deleted_mock = mocker.patch(
        'src.accounts.views.tenants.AuditEventService.tenant_deleted',
    )
    api_client.token_authenticate(master_owner)

    # act
    response = api_client.delete(f'/tenants/{another_tenant.id}')

    # assert
    assert response.status_code == 403
    assert Account.objects.filter(id=another_tenant.id).exists()
    tenant_deleted_mock.assert_not_called()
    increase_plan_users_mock.assert_not_called()
