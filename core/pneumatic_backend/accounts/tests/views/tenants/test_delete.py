import datetime
from django.utils import timezone
import pytest
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
    LeaseLevel,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
)
from pneumatic_backend.accounts.services import (
    AccountService,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.payment.stripe.service import StripeService
from pneumatic_backend.payment.stripe.exceptions import StripeServiceException
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


def test_delete__premium_plan__ok(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.PREMIUM)
    master_account_owner = create_test_user(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='old name',
        plan=BillingPlanType.PREMIUM,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    update_users_counts_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService'
        '.update_users_counts'
    )
    cancel_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'cancel_subscription'
    )
    increase_plan_users_mock = mocker.patch(
        'pneumatic_backend.accounts.views.'
        'tenants.increase_plan_users.delay'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.delete(f'/tenants/{tenant_account.id}')

    # assert
    assert response.status_code == 204
    account_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=master_account,
        user=master_account_owner
    )
    update_users_counts_mock.assert_called_once()
    cancel_subscription_mock.assert_not_called()
    increase_plan_users_mock.assert_called_once_with(
        account_id=master_account.id,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_delete__unlimited_plan__ok(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    master_account_owner = create_test_user(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='old name',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    update_users_counts_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService'
        '.update_users_counts'
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    cancel_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'cancel_subscription'
    )
    increase_plan_users_mock = mocker.patch(
        'pneumatic_backend.accounts.views.'
        'tenants.increase_plan_users.delay'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.delete(f'/tenants/{tenant_account.id}')

    # assert
    assert response.status_code == 204
    account_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=master_account,
        user=master_account_owner
    )
    update_users_counts_mock.assert_called_once()
    increase_plan_users_mock.assert_not_called()
    stripe_service_init_mock.assert_called_once_with(
        user=master_account_owner,
        subscription_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    cancel_subscription_mock.assert_called_once()


def test_delete__fractionalcoo_plan__ok(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.FRACTIONALCOO)
    master_account_owner = create_test_user(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='old name',
        plan=BillingPlanType.FRACTIONALCOO,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    update_users_counts_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService'
        '.update_users_counts'
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    cancel_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'cancel_subscription'
    )
    increase_plan_users_mock = mocker.patch(
        'pneumatic_backend.accounts.views.'
        'tenants.increase_plan_users.delay'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.delete(f'/tenants/{tenant_account.id}')

    # assert
    assert response.status_code == 204
    account_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=master_account,
        user=master_account_owner
    )
    update_users_counts_mock.assert_called_once()
    increase_plan_users_mock.assert_not_called()
    stripe_service_init_mock.assert_called_once_with(
        user=master_account_owner,
        subscription_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    cancel_subscription_mock.assert_called_once()


def test_delete__free_plan__permission_denied(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.FREEMIUM)
    master_account_owner = create_test_user(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='old name',
        plan=BillingPlanType.FREEMIUM,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    update_users_counts_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService'
        '.update_users_counts'
    )
    cancel_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'cancel_subscription'
    )
    increase_plan_users_mock = mocker.patch(
        'pneumatic_backend.accounts.views.'
        'tenants.increase_plan_users.delay'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.delete(f'/tenants/{tenant_account.id}')

    # assert
    assert response.status_code == 403
    account_service_init_mock.assert_not_called()
    update_users_counts_mock.assert_not_called()
    increase_plan_users_mock.assert_not_called()
    cancel_subscription_mock.assert_not_called()


def test_delete__not_exists__permission_denied(api_client, mocker):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    master_account_owner = create_test_user(account=master_account)
    api_client.token_authenticate(master_account_owner)
    cancel_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'cancel_subscription'
    )

    # act
    response = api_client.delete('/tenants/123')

    # assert
    assert response.status_code == 403
    cancel_subscription_mock.assert_not_called()


def test_delete__another_account_tenant__permission_denied(mocker, api_client):

    # arrange
    master_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    master_account_owner = create_test_user(account=master_account)
    another_tenant_account = create_test_account(
        name='tenant',
        tenant_name='old name',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
    )
    create_test_user(
        account=another_tenant_account,
        email='tenant_owner@test.test'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.delete(f'/tenants/{another_tenant_account.id}')

    # assert
    assert response.status_code == 403


def test_delete__another_account_not_tenant__permission_denied(
    api_client,
    mocker
):

    # arrange
    master_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    master_account_owner = create_test_user(account=master_account)
    another_account = create_test_account(
        name='another',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.STANDARD,
    )
    create_test_user(
        account=another_account,
        email='another_owner@test.test'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.delete(f'/tenants/{another_account.id}')

    # assert
    assert response.status_code == 403


def test_delete__tenant__permission_denied(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT
    )
    master_account_owner = create_test_user(account=master_account)
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.delete('/tenants/123')

    # assert
    assert response.status_code == 403


def test_delete__expired_subscription__permission_denied(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - datetime.timedelta(hours=1)
    )
    master_account_owner = create_test_user(account=master_account)
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.delete('/tenants/123')

    # assert
    assert response.status_code == 403


def test_delete__not_admin__permission_denied(
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
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_not_admin)

    # act
    response = api_client.delete('/tenants/123')

    # assert
    assert response.status_code == 403


def test_delete__not_authenticated__auth_error(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT
    )
    create_test_user(account=master_account)
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}

    # act
    response = api_client.delete('/tenants/123')

    # assert
    assert response.status_code == 401


def test_delete__stripe_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.UNLIMITED)
    master_account_owner = create_test_user(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='old name',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    update_users_counts_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService'
        '.update_users_counts'
    )
    message = 'message'
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
        side_effect=StripeServiceException(message)
    )
    cancel_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'cancel_subscription'
    )
    increase_plan_users_mock = mocker.patch(
        'pneumatic_backend.accounts.views.'
        'tenants.increase_plan_users.delay'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.delete(f'/tenants/{tenant_account.id}')

    # assert
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    stripe_service_init_mock.assert_called_once_with(
        user=master_account_owner,
        subscription_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    cancel_subscription_mock.assert_not_called()
    account_service_init_mock.assert_not_called()
    update_users_counts_mock.assert_not_called()
    increase_plan_users_mock.assert_not_called()


@pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
def test_delete__disable_billing__permission_denied(
    plan,
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=plan)
    master_account_owner = create_test_user(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='old name',
        plan=plan,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    account_service_init_mock = mocker.patch.object(
        AccountService,
        attribute='__init__',
        return_value=None
    )
    update_users_counts_mock = mocker.patch(
        'pneumatic_backend.accounts.services.AccountService'
        '.update_users_counts'
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    cancel_subscription_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'cancel_subscription'
    )
    increase_plan_users_mock = mocker.patch(
        'pneumatic_backend.accounts.views.'
        'tenants.increase_plan_users.delay'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': False}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.delete(f'/tenants/{tenant_account.id}')

    # assert
    assert response.status_code == 204
    account_service_init_mock.assert_called_once_with(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=master_account,
        user=master_account_owner
    )
    update_users_counts_mock.assert_called_once()
    increase_plan_users_mock.assert_not_called()
    stripe_service_init_mock.assert_not_called()
    cancel_subscription_mock.assert_not_called()
