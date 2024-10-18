# pylint:disable=redefined-outer-name
import pytest
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from pneumatic_backend.payment.enums import BillingPeriod
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
    LeaseLevel,
)
from pneumatic_backend.accounts.tests.fixtures import (
    create_test_owner,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_template,
    create_test_account,
    create_test_user,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_guest
)
from pneumatic_backend.accounts.services.account import AccountService
from pneumatic_backend.utils.dates import date_format


pytestmark = pytest.mark.django_db


def test_plan__freemium__ok(api_client):

    # arrange
    name = 'New name'
    account = create_test_account(
        name=name,
        plan=BillingPlanType.FREEMIUM
    )
    user = create_test_user(account=account)
    create_test_user(
        account=account,
        email='admin@t.t',

    )
    create_test_template(
        user=user,
        is_active=True,
        tasks_count=1
    )
    create_test_template(
        user=user,
        is_active=False,
        tasks_count=1
    )

    service = AccountService(instance=account, user=user)
    service.update_users_counts()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v2/accounts/plan')

    # assert
    assert response.status_code == 200
    assert response.data['billing_period'] is None
    assert response.data['billing_plan'] == BillingPlanType.FREEMIUM
    assert response.data['billing_sync'] is True
    assert response.data['plan_expiration'] is None
    assert response.data['plan_expiration_tsp'] is None
    assert response.data['trial_ended'] is False
    assert response.data['trial_is_active'] is False
    assert response.data['active_templates'] == 1
    assert response.data['active_users'] == 2
    assert response.data['tenants_active_users'] == 0
    assert response.data['is_subscribed'] is False
    assert response.data['max_templates'] == (
        settings.PAYWALL_MAX_ACTIVE_TEMPLATES
    )
    assert response.data['max_users'] == settings.FREEMIUM_MAX_USERS


def test_plan__premium__ok(api_client):

    # arrange
    name = 'New name'
    plan_expiration = timezone.now() + timedelta(days=30)
    account = create_test_account(
        name=name,
        plan=BillingPlanType.PREMIUM,
        plan_expiration=plan_expiration,
        trial_start=None,
        trial_end=None,
        trial_ended=False,
    )
    user = create_test_user(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v2/accounts/plan')

    # assert
    assert response.status_code == 200
    assert response.data['billing_plan'] == BillingPlanType.PREMIUM
    assert response.data['billing_sync'] is True
    assert response.data['billing_period'] == BillingPeriod.MONTHLY
    assert response.data['plan_expiration'] == plan_expiration.strftime(
        date_format
    )
    assert response.data['plan_expiration_tsp'] == plan_expiration.timestamp()
    assert response.data['trial_ended'] is False
    assert response.data['trial_is_active'] is False
    assert response.data['active_templates'] == 0
    assert response.data['active_users'] == 1
    assert response.data['tenants_active_users'] == 0
    assert response.data['is_subscribed'] is True
    assert response.data['max_templates'] is None
    assert response.data['max_users'] == settings.FREEMIUM_MAX_USERS


def test_plan__premium_with_tenants__ok(api_client):

    # arrange
    name = 'New name'
    plan_expiration = timezone.now() + timedelta(days=30)
    master_account = create_test_account(
        name=name,
        plan=BillingPlanType.PREMIUM,
        plan_expiration=plan_expiration,
        trial_start=None,
        trial_end=None,
        trial_ended=False,
    )
    user = create_test_user(account=master_account)

    tenant_account = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    create_test_user(account=tenant_account, email='t@t.t')
    service = AccountService(instance=master_account, user=user)
    service.update_users_counts()

    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v2/accounts/plan')

    # assert
    assert response.status_code == 200
    assert response.data['billing_plan'] == BillingPlanType.PREMIUM
    assert response.data['billing_sync'] is True
    assert response.data['plan_expiration'] == plan_expiration.strftime(
        date_format
    )
    assert response.data['plan_expiration_tsp'] == plan_expiration.timestamp()
    assert response.data['trial_ended'] is False
    assert response.data['trial_is_active'] is False
    assert response.data['active_templates'] == 0
    assert response.data['active_users'] == 1
    assert response.data['tenants_active_users'] == 1
    assert response.data['is_subscribed'] is True
    assert response.data['max_templates'] is None
    assert response.data['max_users'] == settings.FREEMIUM_MAX_USERS


def test_plan__premium_trial__ok(api_client):

    # arrange
    name = 'New name'
    trail_start = timezone.now() - timedelta(minutes=1)
    plan_expiration = timezone.now() + timedelta(days=30)
    account = create_test_account(
        name=name,
        plan=BillingPlanType.PREMIUM,
        plan_expiration=plan_expiration,
        trial_start=trail_start,
        trial_end=plan_expiration,
        trial_ended=False,
    )
    user = create_test_user(account=account)
    service = AccountService(instance=account, user=user)
    service.update_users_counts()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v2/accounts/plan')

    # assert
    assert response.status_code == 200
    assert response.data['billing_plan'] == BillingPlanType.PREMIUM
    assert response.data['billing_sync'] is True
    assert response.data['billing_period'] == BillingPeriod.MONTHLY
    assert response.data['plan_expiration'] == (
        plan_expiration.strftime(date_format)
    )
    assert response.data['plan_expiration_tsp'] == plan_expiration.timestamp()
    assert response.data['trial_ended'] is False
    assert response.data['trial_is_active'] is True
    assert response.data['active_templates'] == 0
    assert response.data['active_users'] == 1
    assert response.data['tenants_active_users'] == 0
    assert response.data['is_subscribed'] is True
    assert response.data['max_templates'] is None
    assert response.data['max_users'] == settings.FREEMIUM_MAX_USERS


def test_plan__partner__ok(api_client):

    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        lease_level=LeaseLevel.PARTNER,
        max_users=3
    )
    user = create_test_user(account=master_account)
    tenant_account = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    create_test_user(account=tenant_account, email='t@t.t')

    service = AccountService(instance=master_account, user=user)
    service.update_users_counts()

    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v2/accounts/plan')

    # assert
    assert response.status_code == 200
    assert response.data['billing_plan'] == BillingPlanType.PREMIUM
    assert response.data['billing_sync'] is True
    assert response.data['billing_period'] == BillingPeriod.MONTHLY
    assert response.data['plan_expiration'] == (
        master_account.plan_expiration.strftime(date_format)
    )
    assert response.data['plan_expiration_tsp'] == (
        master_account.plan_expiration.timestamp()
    )
    assert response.data['trial_ended'] is False
    assert response.data['trial_is_active'] is False
    assert response.data['active_templates'] == 0
    assert response.data['active_users'] == 1
    assert response.data['tenants_active_users'] == 1
    assert response.data['is_subscribed'] is True
    assert response.data['max_templates'] is None
    assert response.data['max_users'] == 3


def test_plan__tenant__ok(api_client):

    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        lease_level=LeaseLevel.PARTNER,
        max_users=2
    )
    create_test_user(account=master_account)
    tenant_account = create_test_account(
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_user = create_test_user(account=tenant_account, email='t@t.t')
    service = AccountService(instance=tenant_account, user=tenant_user)
    service.update_users_counts()

    api_client.token_authenticate(tenant_user)

    # act
    response = api_client.get('/v2/accounts/plan')

    # assert
    assert response.status_code == 200
    assert response.data['billing_plan'] == BillingPlanType.PREMIUM
    assert response.data['billing_sync'] is True
    assert response.data['billing_period'] == BillingPeriod.MONTHLY
    assert response.data['plan_expiration'] == (
        master_account.plan_expiration.strftime(date_format)
    )
    assert response.data['plan_expiration_tsp'] == (
        master_account.plan_expiration.timestamp()
    )
    assert response.data['trial_ended'] is False
    assert response.data['trial_is_active'] is False
    assert response.data['active_templates'] == 0
    assert response.data['active_users'] == 1
    assert response.data['tenants_active_users'] == 0
    assert response.data['is_subscribed'] is True
    assert response.data['max_templates'] is None
    assert response.data['max_users'] == 2


def test_plan__guest__ok(api_client):

    # arrange
    account_owner = create_test_owner()
    create_test_guest(account=account_owner.account)
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get('/v2/accounts/plan')

    # assert
    assert response.status_code == 200
    assert response.data['active_users'] == 1
    assert response.data['trial_is_active'] is False
    assert response.data['billing_period'] is None


def test_plan__disable_billing_sync__ok(api_client):

    # arrange
    account = create_test_account(billing_sync=False)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/v2/accounts/plan')

    # assert
    assert response.status_code == 200
    assert response.data['billing_sync'] is False
