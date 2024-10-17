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


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('plan', BillingPlanType.PAYMENT_PLANS)
def test_count__any_premium_plan__ok(
    plan,
    api_client,
):
    # arrange
    master_account = create_test_account(
        plan=plan,
        lease_level=LeaseLevel.STANDARD
    )
    master_account_owner = create_test_user(account=master_account)
    create_test_account(
        name='tenant 1',
        plan=plan,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )
    create_test_account(
        name='tenant 2',
        plan=plan,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account
    )

    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.get('/tenants/count')

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 2


def test_count__tenant__permission_denied(
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
    response = api_client.get('/tenants/count')

    # assert
    assert response.status_code == 403


def test_count__not_subscribed__permission_denied(
    api_client,
):
    # arrange
    account = create_test_account(plan=BillingPlanType.FREEMIUM)
    account_owner = create_test_user(account=account)
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get('/tenants/count')

    # assert
    assert response.status_code == 403


def test_count__expired_subscription__permission_denied(
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
    response = api_client.get('/tenants/count')

    # assert
    assert response.status_code == 403


def test_count__not_admin__permission_denied(
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
    response = api_client.get('/tenants/count')

    # assert
    assert response.status_code == 403


def test_count__not_authenticated__auth_error(
    api_client,
):

    # act
    response = api_client.get('/tenants/count')

    # assert
    assert response.status_code == 401
