from datetime import timedelta
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
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.payment.stripe.service import StripeService
from pneumatic_backend.payment.stripe.exceptions import StripeServiceException
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.utils.dates import date_format


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
def test_update__any_premium_plan__ok(
    plan,
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=plan,
        plan_expiration=timezone.now() + timedelta(days=1)
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='old name',
        plan=plan,
        plan_expiration=timezone.now() + timedelta(days=1),
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    update_subscription_description_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_subscription_description'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.patch(
        f'/tenants/{tenant_account.id}',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == tenant_account.id
    assert response.data['tenant_name'] == tenant_name
    assert response.data['date_joined'] == (
        tenant_account.date_joined.strftime(date_format)
    )
    assert response.data['date_joined_tsp'] == (
        tenant_account.date_joined.timestamp()
    )
    stripe_service_init_mock.assert_called_once_with(
        user=master_account_owner,
        subscription_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    update_subscription_description_mock.assert_called_once()


def test_update__same_tenant_name__ok(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan_expiration=timezone.now() + timedelta(hours=1),
        plan=BillingPlanType.UNLIMITED
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'
    tenant_account = create_test_account(
        name='tenant',
        tenant_name=tenant_name,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
        plan_expiration=timezone.now() + timedelta(hours=1),
        plan=BillingPlanType.UNLIMITED
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    update_subscription_description_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_subscription_description'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.patch(
        f'/tenants/{tenant_account.id}',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == tenant_account.id
    assert response.data['tenant_name'] == tenant_name
    assert response.data['date_joined'] == (
        tenant_account.date_joined.strftime(date_format)
    )
    assert response.data['date_joined_tsp'] == (
        tenant_account.date_joined.timestamp()
    )
    stripe_service_init_mock.assert_not_called()
    update_subscription_description_mock.assert_not_called()


def test_update__free_plan__permission_denied(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(plan=BillingPlanType.FREEMIUM)
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'
    update_subscription_description_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_subscription_description'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.patch(
        '/tenants/123321',
        data={
            'tenant_name': tenant_name
        }
    )
    # assert
    assert response.status_code == 403
    update_subscription_description_mock.assert_not_called()


def test_update_not_exists__permission_denied(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() + timedelta(hours=1)
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'
    update_subscription_description_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_subscription_description'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.patch(
        f'/tenants/123',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 403
    update_subscription_description_mock.assert_not_called()


def test_update__another_account_tenant__permission_denied(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan_expiration=timezone.now() + timedelta(hours=1),
        plan=BillingPlanType.UNLIMITED
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'
    tenant_account = create_test_account(
        name='tenant',
        plan_expiration=timezone.now() + timedelta(hours=1),
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    update_subscription_description_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_subscription_description'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.patch(
        f'/tenants/{tenant_account.id}',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 403
    update_subscription_description_mock.assert_not_called()


def test_update__another_account_not_tenant__permission_denied(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan_expiration=timezone.now() + timedelta(hours=1),
        plan=BillingPlanType.UNLIMITED
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'
    another_account = create_test_account(
        name='another',
        lease_level=LeaseLevel.STANDARD,
        plan_expiration=timezone.now() + timedelta(hours=1),
        plan=BillingPlanType.UNLIMITED,
    )
    create_test_user(
        account=another_account,
        email='another_owner@test.test'
    )
    update_subscription_description_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_subscription_description'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.patch(
        f'/tenants/{another_account.id}',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 403
    update_subscription_description_mock.assert_not_called()


def test_update__stripe_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() + timedelta(days=1)
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='old name',
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() + timedelta(days=1),
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    message = 'message'
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
        side_effect=StripeServiceException(message)
    )
    update_subscription_description_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_subscription_description',
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.patch(
        f'/tenants/{tenant_account.id}',
        data={
            'tenant_name': 'tenant_name'
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    stripe_service_init_mock.assert_called_once_with(
        user=master_account_owner,
        subscription_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    update_subscription_description_mock.assert_not_called()


def test_update__blank_tenant_name__validation_error(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan_expiration=timezone.now() + timedelta(hours=1),
        plan=BillingPlanType.UNLIMITED,
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='old name',
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
        plan_expiration=timezone.now() + timedelta(hours=1),
        plan=BillingPlanType.UNLIMITED,
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    update_subscription_description_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_subscription_description'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.patch(
        f'/tenants/{tenant_account.id}',
        data={
            'tenant_name': ''
        }
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be blank.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'tenant_name'
    assert response.data['message'] == message
    update_subscription_description_mock.assert_not_called()


def test_update__null_tenant_name__validation_error(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan_expiration=timezone.now() + timedelta(hours=1),
        plan=BillingPlanType.UNLIMITED,
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='old name',
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
        plan_expiration=timezone.now() + timedelta(hours=1),
        plan=BillingPlanType.UNLIMITED,
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    update_subscription_description_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_subscription_description'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.patch(
        f'/tenants/{tenant_account.id}',
        data={
            'tenant_name': None
        }
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'tenant_name'
    assert response.data['message'] == message
    update_subscription_description_mock.assert_not_called()


def test_update__skip_tenant_name__not_change(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan_expiration=timezone.now() + timedelta(hours=1),
        plan=BillingPlanType.UNLIMITED,
    )
    master_account_owner = create_test_user(account=master_account)
    old_tenant_name = 'old name'
    tenant_account = create_test_account(
        name='tenant',
        tenant_name=old_tenant_name,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
        plan_expiration=timezone.now() + timedelta(hours=1),
        plan=BillingPlanType.UNLIMITED,
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    update_subscription_description_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_subscription_description'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.patch(
        f'/tenants/{tenant_account.id}',
        data={}
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == tenant_account.id
    assert response.data['tenant_name'] == old_tenant_name
    assert response.data['date_joined']
    stripe_service_init_mock.assert_not_called()
    update_subscription_description_mock.assert_not_called()


def test_update__tenant__permission_denied(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan_expiration=timezone.now() + timedelta(hours=1),
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'
    update_subscription_description_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_subscription_description'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.patch(
        '/tenants/123',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 403
    update_subscription_description_mock.assert_not_called()


def test_update__expired_subscription__permission_denied(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - timedelta(hours=1)
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'
    update_subscription_description_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_subscription_description'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.patch(
        '/tenants/123321',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 403
    update_subscription_description_mock.assert_not_called()


def test_update__not_admin__permission_denied(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan_expiration=timezone.now() + timedelta(hours=1),
        plan=BillingPlanType.UNLIMITED,
    )
    master_account_not_admin = create_test_user(
        account=master_account,
        is_admin=False,
        is_account_owner=False
    )
    tenant_name = 'some name'
    update_subscription_description_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_subscription_description'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}
    api_client.token_authenticate(master_account_not_admin)

    # act
    response = api_client.patch(
        '/tenants/123321',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 403
    update_subscription_description_mock.assert_not_called()


def test_update__not_authenticated__auth_error(
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan_expiration=timezone.now() + timedelta(hours=1),
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT
    )
    create_test_user(account=master_account)
    tenant_name = 'some name'
    update_subscription_description_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_subscription_description'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': True}

    # act
    response = api_client.patch(
        '/tenants/123',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 401
    update_subscription_description_mock.assert_not_called()


@pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
def test_update__disable_billing__ok(
    plan,
    mocker,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=plan,
        plan_expiration=timezone.now() + timedelta(days=1)
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_name = 'some name'
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='old name',
        plan=plan,
        plan_expiration=timezone.now() + timedelta(days=1),
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    update_subscription_description_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'update_subscription_description'
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.accounts.views.tenants.settings'
    )
    settings_mock.PROJECT_CONF = {'BILLING': False}
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.patch(
        f'/tenants/{tenant_account.id}',
        data={
            'tenant_name': tenant_name
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == tenant_account.id
    assert response.data['tenant_name'] == tenant_name
    assert response.data['date_joined']
    stripe_service_init_mock.assert_not_called()
    update_subscription_description_mock.assert_not_called()
