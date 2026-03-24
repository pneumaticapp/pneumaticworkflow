import pytest
from datetime import timedelta

from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.accounts.messages import MSG_A_0035, MSG_A_0037, MSG_A_0041
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_dataset,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_retrieve__unauthenticated__unauthorized(api_client):

    """Unauthenticated user — 401"""

    # arrange
    account = create_test_account()
    dataset = create_test_dataset(account=account)

    # act
    response = api_client.get(f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 401


def test_retrieve__expired_subscription__permission_denied(api_client):

    """Expired subscription — 403"""

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035


def test_retrieve__billing_plan__permission_denied(api_client):

    """Billing plan restriction — 403"""

    # arrange
    account = create_test_account(plan=None)
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041


def test_retrieve__users_overlimited__permission_denied(api_client):

    """Users overlimited — 403"""

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        max_users=1,
    )
    user = create_test_owner(account=account)
    create_test_not_admin(
        account=account,
        email='extra@pneumatic.app',
    )
    account.active_users = 2
    account.save()
    dataset = create_test_dataset(account=account)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037


def test_retrieve__not_found__not_found(api_client):

    """Non-existent dataset id — 404"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    non_existent_id = 999999

    # act
    response = api_client.get(f'/datasets/{non_existent_id}')

    # assert
    assert response.status_code == 404


def test_retrieve__another_account__not_found(api_client):

    """Dataset belonging to another account — 404"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)

    another_account = create_test_account(name='Another Company')
    dataset = create_test_dataset(account=another_account)

    # act
    response = api_client.get(f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 404


def test_retrieve__ok(api_client):

    """Valid request — 200"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(
        account=account,
        name='My Dataset',
        description='Desc',
        items_count=2,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == dataset.id
    assert response.data['name'] == dataset.name
    assert response.data['description'] == dataset.description
    assert len(response.data['items']) == 2
