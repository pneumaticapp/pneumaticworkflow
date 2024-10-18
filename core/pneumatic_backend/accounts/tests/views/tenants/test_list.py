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
from pneumatic_backend.utils.dates import date_format


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
def test_list__any_premium_plan__ok(
    plan,
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
    create_test_user(
        account=tenant_account,
        email='tenant_owner@test.test'
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.get('/tenants')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == tenant_account.id
    assert response.data[0]['tenant_name'] == tenant_account.tenant_name
    assert response.data[0]['date_joined'] == (
        tenant_account.date_joined.strftime(date_format)
    )
    assert response.data[0]['date_joined_tsp'] == (
        tenant_account.date_joined.timestamp()
    )


def test_list__free__permission_denied(
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.FREEMIUM,
        lease_level=LeaseLevel.STANDARD
    )
    master_account_owner = create_test_user(account=master_account)
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.get('/tenants')

    # assert
    assert response.status_code == 403


def test_list__tenant__permission_denied(
    api_client,
):
    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
    )
    master_account_owner = create_test_user(account=account)
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.get('/tenants')

    # assert
    assert response.status_code == 403


def test_list__expired_subscription__permission_denied(
    api_client,
):
    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - datetime.timedelta(hours=1)
    )
    account_owner = create_test_user(account=account)
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get('/tenants')

    # assert
    assert response.status_code == 403


def test_list__not_admin__permission_denied(
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
    )
    master_account_owner = create_test_user(
        account=master_account,
        is_account_owner=False,
        is_admin=False
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.get('/tenants')

    # assert
    assert response.status_code == 403


def test_list__not_authenticated__auth_error(
    api_client,
):

    # act
    response = api_client.get('/tenants')

    # assert
    assert response.status_code == 401


def test_list__ordering_by_tenant_name__ok(
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='second tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_account_2 = create_test_account(
        name='tenant',
        tenant_name='first tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.get('/tenants?ordering=tenant_name')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == tenant_account_2.id
    assert response.data[1]['id'] == tenant_account.id


def test_list__default_ordering__ok(
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='second tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_account_2 = create_test_account(
        name='tenant',
        tenant_name='first tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.get('/tenants')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == tenant_account_2.id
    assert response.data[1]['id'] == tenant_account.id


def test_list__ordering_by_reverse_tenant_name__ok(
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        tenant_name='second tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_account_2 = create_test_account(
        name='tenant',
        tenant_name='first tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.get('/tenants?ordering=-tenant_name')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == tenant_account.id
    assert response.data[1]['id'] == tenant_account_2.id


def test_list__ordering_by_date_joined__ok(
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_account = create_test_account(
        name='second tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_account_2 = create_test_account(
        name='first tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_account_2.date_joined = (
        tenant_account_2.date_joined - datetime.timedelta(hours=1)
    )
    tenant_account_2.save(update_fields=['date_joined'])
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.get('/tenants?ordering=date_joined')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == tenant_account_2.id
    assert response.data[1]['id'] == tenant_account.id


def test_list__ordering_by_reverse_date_joined__ok(
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
    )
    master_account_owner = create_test_user(account=master_account)
    tenant_account = create_test_account(
        name='second tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_account_2 = create_test_account(
        name='first tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    tenant_account_2.date_joined = (
        tenant_account_2.date_joined - datetime.timedelta(hours=1)
    )
    tenant_account_2.save(update_fields=['date_joined'])
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.get('/tenants?ordering=-date_joined')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == tenant_account.id
    assert response.data[1]['id'] == tenant_account_2.id


def test_list__invalid_ordering__validation_error(
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
    )
    master_account_owner = create_test_user(
        account=master_account,
    )
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.get('/tenants?ordering=invalid')

    # assert
    assert response.status_code == 400
    assert str(response.data['ordering'][0]) == (
        'Select a valid choice. '
        'invalid is not one of the available choices.'
    )
