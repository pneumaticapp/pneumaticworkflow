import pytest
from datetime import timedelta
from django.utils import timezone
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
    create_test_guest,
    create_test_workflow,
    create_test_group,
)
from pneumatic_backend.processes.models import TaskPerformer
from pneumatic_backend.accounts.enums import (
    UserDateFormat,
    BillingPlanType,
)
from pneumatic_backend.authentication.services import GuestJWTAuthService
from pneumatic_backend.utils.dates import date_format


pytestmark = pytest.mark.django_db


def test_list__ok(api_client):

    # arrange
    user = create_test_user()
    group_1 = create_test_group(
        name='group_1',
        user=user,
        users=[user, ]
    )
    group_2 = create_test_group(
        name='group_2',
        user=user,
        users=[user, ]
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(path='/accounts/user')

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['id'] == user.id
    assert data['email'] == user.email
    assert data['photo'] == user.photo
    assert data['phone'] == user.phone
    assert data['first_name'] == user.first_name
    assert data['last_name'] == user.last_name
    assert data['type'] == user.type
    assert data['date_joined'] == user.date_joined.strftime(date_format)
    assert data['date_joined_tsp'] == user.date_joined.timestamp()
    assert data['is_admin'] == user.is_admin
    assert data['is_staff'] == user.is_admin
    assert data['is_account_owner'] == user.is_account_owner
    assert data['language'] == user.language
    assert data['timezone'] == user.timezone
    assert data['date_fmt'] == UserDateFormat.API_USA_12
    assert data['date_fdw'] == user.date_fdw
    assert data['invite'] is None
    assert data['groups'] == [group_1.id, group_2.id]
    assert data['is_tasks_digest_subscriber'] == (
        user.is_tasks_digest_subscriber
    )
    assert data['is_digest_subscriber'] == user.is_digest_subscriber
    assert data['is_comments_mentions_subscriber'] == (
        user.is_comments_mentions_subscriber
    )
    assert data['is_new_tasks_subscriber'] == user.is_new_tasks_subscriber
    assert data['is_complete_tasks_subscriber'] == (
        user.is_complete_tasks_subscriber
    )
    assert data['is_newsletters_subscriber'] == user.is_newsletters_subscriber
    assert data['is_special_offers_subscriber'] == (
        user.is_special_offers_subscriber
    )


def test_list__guest__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_user(is_account_owner=True, account=account)
    guest = create_test_guest(account=account)
    workflow = create_test_workflow(owner, tasks_count=1)
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id
    )

    # act
    response = api_client.get(
        path='/accounts/user',
        **{'X-Guest-Authorization': str_token}
    )

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['id'] == guest.id
    assert data['email'] == guest.email
    assert data['photo'] == guest.photo
    assert data['phone'] == guest.phone
    assert data['first_name'] == guest.first_name
    assert data['last_name'] == guest.last_name
    assert data['type'] == guest.type
    assert data['date_joined'] == guest.date_joined.strftime(date_format)
    assert data['date_joined_tsp'] == guest.date_joined.timestamp()
    assert data['is_admin'] == guest.is_admin
    assert data['is_staff'] == guest.is_admin
    assert data['is_account_owner'] == guest.is_account_owner
    assert data['language'] == guest.language
    assert data['timezone'] == guest.timezone
    assert data['date_fmt'] == UserDateFormat.API_USA_12
    assert data['date_fdw'] == guest.date_fdw
    assert data['invite'] is None
    assert data['is_tasks_digest_subscriber'] == (
        guest.is_tasks_digest_subscriber
    )
    assert data['is_digest_subscriber'] == guest.is_digest_subscriber
    assert data['is_comments_mentions_subscriber'] == (
        guest.is_comments_mentions_subscriber
    )
    assert data['is_new_tasks_subscriber'] == guest.is_new_tasks_subscriber
    assert data['is_complete_tasks_subscriber'] == (
        guest.is_complete_tasks_subscriber
    )
    assert data['is_newsletters_subscriber'] == guest.is_newsletters_subscriber
    assert data['is_special_offers_subscriber'] == (
        guest.is_special_offers_subscriber
    )


def test_list__not_authenticated__unauthorized(api_client):

    # act
    response = api_client.get(path='/accounts/user')

    # assert
    assert response.status_code == 401


def test_list__payment_card_not_provided__permission_denied(api_client):

    # arrange
    account = create_test_account(payment_card_provided=False)
    user = create_test_user(is_account_owner=True, account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(path='/accounts/user')

    # assert
    assert response.status_code == 403


def test_list__expired_subscription__ok(api_client):

    # arrange
    account = create_test_account(
        plan=BillingPlanType.UNLIMITED,
        plan_expiration=timezone.now() - timedelta(days=1)
    )
    user = create_test_user(is_account_owner=True, account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(path='/accounts/user')

    # assert
    assert response.status_code == 200
    data = response.data
    assert data['id'] == user.id
