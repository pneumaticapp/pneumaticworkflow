import datetime
from django.utils import timezone
import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_group,
    create_test_account
)
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
)

pytestmark = pytest.mark.django_db


def test_list_ok(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user_1 = create_test_user(account=account)
    user_2 = create_test_user(email='1@test.com', account=account)
    user_3 = create_test_user(email='2@test.com', account=account)
    create_test_user(email='3@test.com', account=account)
    api_client.token_authenticate(user_1)
    group_1 = create_test_group(user=user_1, users=[user_1, user_3])
    group_2 = create_test_group(user=user_1, users=[user_2])

    # act
    response = api_client.get(
        path='/accounts/groups'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    data_group_1 = response.data[0]
    assert data_group_1['name'] == group_1.name
    assert data_group_1['photo'] == group_1.photo
    assert data_group_1['users'] == [user_1.id, user_3.id]
    data_group_2 = response.data[1]
    assert data_group_2['name'] == group_2.name
    assert data_group_2['photo'] == group_2.photo
    assert data_group_2['users'] == [user_2.id]


def test_list__not_admin__permission_denied(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    create_test_group(user=user, users=[user, ])
    no_admin_user = create_test_user(
        account=account,
        email='no_admin@test.com',
        is_admin=False,
        is_account_owner=False
    )

    api_client.token_authenticate(no_admin_user)

    # act
    response = api_client.get(
        path='/accounts/groups'
    )

    # assert
    assert response.status_code == 403


def test_list__not_auth__permission_denied(api_client):

    # arrange
    user = create_test_user()
    create_test_group(user=user, users=[user, ])

    # act
    response = api_client.get(
        path='/accounts/groups'
    )

    # assert
    assert response.status_code == 401


def test_list__expired_subscription__ok(api_client):

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
        path='/accounts/groups'
    )

    # assert
    assert response.status_code == 200
    data = response.data[0]
    assert data['name'] == group.name
    assert data['photo'] == group.photo
    assert data['users'][0] == user.id


def test_list__default_ordering__ok(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    group_1 = create_test_group(name='test_3', user=user)
    group_2 = create_test_group(name='test_1', user=user)
    group_3 = create_test_group(name='test_2', user=user)

    # act
    response = api_client.get(
        path='/accounts/groups'
    )

    # assert
    assert response.status_code == 200
    data = response.data
    assert data[0]['name'] == group_2.name
    assert data[1]['name'] == group_3.name
    assert data[2]['name'] == group_1.name


def test_list__order_by_reverse_name__ok(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    group_1 = create_test_group(name='test_3', user=user)
    group_2 = create_test_group(name='test_1', user=user)
    group_3 = create_test_group(name='test_2', user=user)

    # act
    response = api_client.get(
        path='/accounts/groups?ordering=-name'
    )

    # assert
    assert response.status_code == 200
    data = response.data
    assert data[0]['name'] == group_1.name
    assert data[1]['name'] == group_3.name
    assert data[2]['name'] == group_2.name


def test_list__order_name__ok(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    group_1 = create_test_group(name='test_3', user=user)
    group_2 = create_test_group(name='test_1', user=user)
    group_3 = create_test_group(name='test_2', user=user)

    # act
    response = api_client.get(
        path='/accounts/groups?ordering=name'
    )

    # assert
    assert response.status_code == 200
    data = response.data
    assert data[0]['name'] == group_2.name
    assert data[1]['name'] == group_3.name
    assert data[2]['name'] == group_1.name


@pytest.mark.parametrize('value', ('undefined', None, []))
def test_list__invalid_ordering__validation_error(value, api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.UNLIMITED)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    create_test_group(name='test_3', user=user)
    create_test_group(name='test_1', user=user)
    create_test_group(name='test_2', user=user)

    # act
    response = api_client.get(
        path=f'/accounts/groups?ordering={value}'
    )

    # assert
    message = f'"{value}" is not a valid choice.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'ordering'
