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


def test_retrieve__not_admin__ok(api_client):

    logo_lg = 'https://some-site.com/image.jpg'
    logo_sm = 'https://some-site.com/image-2.jpg'
    name = 'New name'
    account = create_test_account(
        name=name,
        logo_lg=logo_lg,
        logo_sm=logo_sm,
        lease_level=LeaseLevel.TENANT,
        plan=BillingPlanType.PREMIUM
    )
    user = create_test_user(
        account=account,
        is_admin=False,
        is_account_owner=False
    )
    api_client.token_authenticate(user)
    response = api_client.get('/accounts/account')

    assert response.status_code == 200
    assert response.data['id'] == account.id
    assert response.data['name'] == name
    assert response.data['date_joined'] == (
        account.date_joined.strftime(date_format)
    )
    assert response.data['date_joined_tsp'] == (
        account.date_joined.timestamp()
    )
    assert response.data['plan_expiration'] == (
        account.plan_expiration.strftime(date_format)
    )
    assert response.data['plan_expiration_tsp'] == (
        account.plan_expiration.timestamp()
    )
    assert response.data['lease_level'] == LeaseLevel.TENANT
    assert response.data['logo_lg'] == logo_lg
    assert response.data['logo_sm'] == logo_sm
