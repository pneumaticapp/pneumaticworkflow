from datetime import timedelta

import pytest
from django.utils import timezone

from src.accounts.enums import (
    BillingPlanType,
    UserStatus,
    UserType,
)
from src.accounts.messages import (
    MSG_A_0035,
    MSG_A_0036,
    MSG_A_0041,
)
from src.accounts.models import APIKey
from src.authentication.tokens import PneumaticToken
from src.generics.messages import MSG_GE_0001
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_api_key__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_key = APIKey.objects.create(
        user=owner,
        name=owner.get_full_name(),
        account_id=owner.account_id,
        key=PneumaticToken.create(owner, for_api_key=True),
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get('/accounts/users/api-key')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data = response.data[0]
    assert data['first_name'] == owner.first_name
    assert data['last_name'] == owner.last_name
    assert data['email'] == owner.email
    assert data['is_admin'] == owner.is_admin
    assert data['is_account_owner'] == owner.is_account_owner
    assert data['api_key'] == api_key.key
    assert data['type'] == owner.type
    assert data['status'] == owner.status


def test_api_key__pagination__ok(api_client):

    """ Pagination parameters limit=2 offset=1 are ignored """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    create_test_admin(account=account)
    create_test_not_admin(account=account)
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        path='/accounts/users/api-key',
        data={'limit': 2, 'offset': 1},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3


def test_api_key__user_without_api_key__ok(api_client):

    """ User without APIKey — api_key field is null """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_client.token_authenticate(owner)

    # act
    response = api_client.get('/accounts/users/api-key')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['email'] == owner.email
    assert response.data[0]['api_key'] is None


def test_api_key__account_scope__ok(api_client):

    """ Only users from the requester's account are returned """

    # arrange
    account_1 = create_test_account(name='Account 1')
    owner_1 = create_test_owner(account=account_1)
    account_2 = create_test_account(name='Account 2')
    create_test_owner(
        account=account_2,
        email='owner2@test.test',
    )
    create_test_not_admin(
        account=account_2,
        email='user2@test.test',
    )
    api_client.token_authenticate(owner_1)

    # act
    response = api_client.get('/accounts/users/api-key')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['email'] == owner_1.email


def test_api_key__invited_users_included__ok(api_client):

    """ Users with a pending UserInvite are included in results """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited_user = create_invited_user(
        user=owner,
        email='invited@test.test',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get('/accounts/users/api-key')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    # default ordering: last_name asc; '' < 'Doe'
    assert response.data[0]['email'] == invited_user.email
    assert response.data[1]['email'] == owner.email


def test_api_key__filter_type_user__ok(api_client):

    """ Filter type=user returns only regular users """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    create_test_guest(account=account)
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        path='/accounts/users/api-key',
        data={'type': UserType.USER},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['type'] == UserType.USER
    assert response.data[0]['email'] == owner.email


def test_api_key__filter_type_guest__ok(api_client):

    """ Filter type=guest returns only guest users """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    guest = create_test_guest(account=account)
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        path='/accounts/users/api-key',
        data={'type': UserType.GUEST},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['type'] == UserType.GUEST
    assert response.data[0]['email'] == guest.email


def test_api_key__filter_status_active__ok(api_client):

    """ Filter status=active returns only active users """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    create_test_not_admin(
        account=account,
        email='inactive@test.test',
        status=UserStatus.INACTIVE,
    )
    create_invited_user(user=owner, email='invited@test.test')
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        path='/accounts/users/api-key',
        data={'status': UserStatus.ACTIVE},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['status'] == UserStatus.ACTIVE
    assert response.data[0]['email'] == owner.email


def test_api_key__filter_status_invited__ok(api_client):

    """ Filter status=invited returns only invited users """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited_user = create_invited_user(
        user=owner,
        email='invited@test.test',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        path='/accounts/users/api-key',
        data={'status': UserStatus.INVITED},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['status'] == UserStatus.INVITED
    assert response.data[0]['email'] == invited_user.email


def test_api_key__filter_status_inactive__ok(api_client):

    """ Filter status=inactive returns only inactive users """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    inactive_user = create_test_not_admin(
        account=account,
        email='inactive@test.test',
        status=UserStatus.INACTIVE,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        path='/accounts/users/api-key',
        data={'status': UserStatus.INACTIVE},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['status'] == UserStatus.INACTIVE
    assert response.data[0]['email'] == inactive_user.email


def test_api_key__filter_groups__ok(api_client):

    """ Filter groups returns only users belonging to the group """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_in_group = create_test_not_admin(
        account=account,
        email='ingroup@test.test',
    )
    create_test_not_admin(
        account=account,
        email='outside@test.test',
    )
    group = create_test_group(
        account=account,
        users=[user_in_group],
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        path=f'/accounts/users/api-key?groups={group.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['email'] == user_in_group.email


def test_api_key__ordering_first_name__ok(api_client):

    """ ordering=first_name sorts results ascending by first name """

    # arrange
    account = create_test_account()
    owner = create_test_owner(
        account=account,
        first_name='Beta',
    )
    user_1 = create_test_not_admin(
        account=account,
        email='alpha@test.test',
        first_name='Alpha',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        path='/accounts/users/api-key',
        data={'ordering': 'first_name'},
    )

    # assert
    assert response.status_code == 200
    assert response.data[0]['email'] == user_1.email
    assert response.data[1]['email'] == owner.email


def test_api_key__ordering_last_name_desc__ok(api_client):

    """ ordering=-last_name sorts results descending by last name """

    # arrange
    account = create_test_account()
    owner = create_test_owner(
        account=account,
        last_name='Alpha',
    )
    user_1 = create_test_not_admin(
        account=account,
        email='beta@test.test',
        last_name='Beta',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        path='/accounts/users/api-key',
        data={'ordering': '-last_name'},
    )

    # assert
    assert response.status_code == 200
    assert response.data[0]['email'] == user_1.email
    assert response.data[1]['email'] == owner.email


def test_api_key__ordering_status__ok(api_client):

    """ ordering=status sorts results ascending by status value """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invited_user = create_invited_user(
        user=owner,
        email='invited@test.test',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        path='/accounts/users/api-key',
        data={'ordering': 'status'},
    )

    # assert
    assert response.status_code == 200
    # 'active' < 'invited' lexicographically
    assert response.data[0]['email'] == owner.email
    assert response.data[1]['email'] == invited_user.email


def test_api_key__unauthenticated__permission_denied(api_client):

    """ Permission: unauthenticated request is rejected """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)

    # act
    response = api_client.get('/accounts/users/api-key')

    # assert
    assert response.status_code == 401


def test_api_key__non_owner__permission_denied(api_client):

    """ Permission: non-owner user is rejected """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    admin = create_test_admin(account=account)
    api_client.token_authenticate(admin)

    # act
    response = api_client.get('/accounts/users/api-key')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0036


def test_api_key__expired_subscription__permission_denied(api_client):

    """ Permission: expired subscription is rejected """

    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    owner = create_test_owner(account=account)
    api_client.token_authenticate(owner)

    # act
    response = api_client.get('/accounts/users/api-key')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035


def test_api_key__no_billing_plan__permission_denied(api_client):

    """ Permission: account without billing plan is rejected """

    # arrange
    account = create_test_account(plan=None)
    owner = create_test_owner(account=account)
    api_client.token_authenticate(owner)

    # act
    response = api_client.get('/accounts/users/api-key')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041


def test_api_key__filter_type_invalid__validation_error(api_client):

    """ Filter type with invalid value returns 400 """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invalid_type = 'invalid_type'
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        path=f'/accounts/users/api-key?type={invalid_type}',
    )

    # assert
    assert response.status_code == 400
    assert response.data[0] == MSG_GE_0001(invalid_type)


def test_api_key__filter_status_invalid__validation_error(api_client):

    """ Filter status with invalid value returns 400 """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invalid_status = 'invalid_status'
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        path=f'/accounts/users/api-key?status={invalid_status}',
    )

    # assert
    assert response.status_code == 400
    assert response.data[0] == MSG_GE_0001(invalid_status)


def test_api_key__ordering_invalid__validation_error(api_client):

    """ Filter ordering with invalid field name returns 400 """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    invalid_ordering = 'invalid_field'
    expected_message = (
        f'Select a valid choice. {invalid_ordering}'
        f' is not one of the available choices.'
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        path=f'/accounts/users/api-key?ordering={invalid_ordering}',
    )

    # assert
    assert response.status_code == 400
    assert str(response.data['ordering'][0]) == expected_message
