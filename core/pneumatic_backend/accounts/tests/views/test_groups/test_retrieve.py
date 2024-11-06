import pytest
import datetime
from django.utils import timezone
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_group,
    create_test_account
)
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
)

pytestmark = pytest.mark.django_db


def test_retrieve__ok(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    group = create_test_group(user=user, users=[user, ])

    # act
    response = api_client.get(
        path=f'/accounts/groups/{group.id}'
    )

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['name'] == group.name
    assert data['photo'] == group.photo
    assert data['users'][0] == user.id


def test_retrieve__not_admin__permission_denied(api_client):
    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    group = create_test_group(user=user, users=[user, ])
    no_admin_user = create_test_user(
        account=account,
        email='no_admin@test.com',
        is_admin=False,
        is_account_owner=False
    )

    api_client.token_authenticate(no_admin_user)

    # act
    response = api_client.get(
        path=f'/accounts/groups/{group.id}'
    )

    # assert
    assert response.status_code == 403


def test_retrieve__not_auth__permission_denied(api_client):
    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    group = create_test_group(user=user, users=[user, ])

    # act
    response = api_client.get(
        path=f'/accounts/groups/{group.id}'
    )

    # assert
    assert response.status_code == 401


def test_retrieve__expired_subscription__ok(api_client):
    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - datetime.timedelta(hours=1)
    )
    user = create_test_user(account=account)
    group = create_test_group(user=user, users=[user, ])
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        path=f'/accounts/groups/{group.id}'
    )

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['name'] == group.name
    assert data['photo'] == group.photo
    assert data['users'][0] == user.id
