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


def test_list__unauthenticated__unauthorized(api_client):

    """Unauthenticated user — 401"""

    # arrange
    account = create_test_account()
    create_test_dataset(account=account)

    # act
    response = api_client.get('/datasets')

    # assert
    assert response.status_code == 401


def test_list__expired_subscription__permission_denied(api_client):

    """Expired subscription — 403"""

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/datasets')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035


def test_list__billing_plan__permission_denied(api_client):

    """Billing plan restriction — 403"""

    # arrange
    account = create_test_account(plan=None)
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/datasets')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041


def test_list__users_overlimited__permission_denied(api_client):

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
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/datasets')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037


def test_list__invalid_ordering__validation_error(api_client):

    """Invalid `ordering` query param value — 400"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/datasets?ordering=invalid_field')

    # assert
    assert response.status_code == 400


def test_list__ordering_by_name_asc__ok(api_client):

    """`ordering=name` — ordered by name asc"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset_a = create_test_dataset(account=account, name='Alpha')
    dataset_z = create_test_dataset(account=account, name='Zeta')
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/datasets?ordering=name')

    # assert
    assert response.status_code == 200
    ids = [item['id'] for item in response.data]
    assert ids[0] == dataset_a.id
    assert ids[1] == dataset_z.id


def test_list__ordering_by_name_desc__ok(api_client):

    """`ordering=-name` — ordered by name desc"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset_a = create_test_dataset(account=account, name='Alpha')
    dataset_z = create_test_dataset(account=account, name='Zeta')
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/datasets?ordering=-name')

    # assert
    assert response.status_code == 200
    ids = [item['id'] for item in response.data]
    assert ids[0] == dataset_z.id
    assert ids[1] == dataset_a.id


def test_list__ordering_by_date_asc__ok(api_client):

    """`ordering=date` — ordered by date_created asc"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset_first = create_test_dataset(account=account, name='First')
    dataset_second = create_test_dataset(account=account, name='Second')
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/datasets?ordering=date')

    # assert
    assert response.status_code == 200
    ids = [item['id'] for item in response.data]
    assert ids[0] == dataset_first.id
    assert ids[1] == dataset_second.id


def test_list__ordering_by_date_desc_default__ok(api_client):

    """`ordering=-date` — ordered by date_created desc (default)"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset_first = create_test_dataset(account=account, name='First')
    dataset_second = create_test_dataset(account=account, name='Second')
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/datasets')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == dataset_first.id
    assert response.data[1]['id'] == dataset_second.id


def test_list__items_count__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_test_dataset(account=account, items_count=3)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/datasets')

    # assert
    assert response.status_code == 200
    assert response.data[0]['items_count'] == 3


def test_list__items_count_after_delete__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, items_count=3)
    dataset.items.get(order=3).delete()
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/datasets')

    # assert
    assert response.status_code == 200
    assert response.data[0]['items_count'] == 2


def test_list__pagination__ok(api_client):

    """Pagination via `limit` and `offset`"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_test_dataset(account=account, name='Dataset 1')
    create_test_dataset(account=account, name='Dataset 2')
    create_test_dataset(account=account, name='Dataset 3')
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/datasets?limit=2&offset=0')

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 3
    assert len(response.data['results']) == 2
