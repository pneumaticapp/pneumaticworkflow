import pytest
from pneumatic_backend.accounts.enums import (
    UserStatus,
    BillingPlanType,
    UserType,
    SourceType,
    UserDateFormat,
)
from pneumatic_backend.accounts.models import (
    UserInvite,
)

from pneumatic_backend.accounts.tests.fixtures import (
    create_test_user,
    create_invited_user,
    create_test_owner,
    create_test_account,
    create_test_group,
)
from pneumatic_backend.processes.models import (
    TaskPerformer,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_guest
)
from pneumatic_backend.authentication.services import GuestJWTAuthService
from pneumatic_backend.accounts.services import (
    UserInviteService
)
from pneumatic_backend.accounts.services.user import UserService
from pneumatic_backend.generics.messages import MSG_GE_0001
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
    response = api_client.get('/accounts/users')

    # assert
    assert response.status_code == 200
    data = response.data[0]
    assert data['id'] == user.id
    assert data['email'] == user.email
    assert data['phone'] == user.phone
    assert data['photo'] == user.photo
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
    assert data['is_digest_subscriber'] == (
        user.is_digest_subscriber
    )
    assert data['is_newsletters_subscriber'] == (
        user.is_newsletters_subscriber
    )
    assert data['is_special_offers_subscriber'] == (
        user.is_special_offers_subscriber
    )
    assert data['is_new_tasks_subscriber'] == (
        user.is_new_tasks_subscriber
    )
    assert data['is_complete_tasks_subscriber'] == (
        user.is_complete_tasks_subscriber
    )
    assert data['is_comments_mentions_subscriber'] == (
        user.is_comments_mentions_subscriber
    )


def test_list__different_types__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_user(
        account=account,
        is_account_owner=True,
        email='owner@test.test',
        last_name='z'
    )
    user = create_test_user(account=account, last_name='y')
    api_client.token_authenticate(user)
    invited_user = create_invited_user(user, last_name='x')
    inactive_user = create_test_user(
        account=account,
        email='test@test.test',
        last_name='p'
    )
    UserService.deactivate(inactive_user)
    guest = create_test_guest(account=account)

    # act
    response = api_client.get('/accounts/users')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 5
    assert response.data[0]['id'] == guest.id
    assert response.data[1]['id'] == inactive_user.id
    assert response.data[2]['id'] == invited_user.id
    assert response.data[3]['id'] == user.id
    assert response.data[4]['id'] == owner.id


def test_list__filter_group__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account,)
    another_user = create_test_user(
        account=account,
        email='test@test.test'
    )
    create_test_user(
        account=account,
        email='additional@test.test'
    )
    group = create_test_group(
        user=user,
        users=[user, another_user, ]
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/users?groups={group.id}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == user.id
    assert response.data[1]['id'] == another_user.id


def test_list__group_multiple_values__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account, first_name='1')
    another_user = create_test_user(
        account=account,
        first_name='2',
        email='test@test.test'
    )
    create_test_user(
        account=account,
        email='additional@test.test'
    )
    group_1 = create_test_group(
        name='test',
        user=user,
        users=[another_user, ]
    )
    group_2 = create_test_group(
        user=user,
        users=[user, ]
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/users?groups={group_1.id},{group_2.id}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == user.id
    assert response.data[1]['id'] == another_user.id


def test_list__status_inactive__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    inactive_user = create_test_user(
        account=account,
        email='test@test.test'
    )

    UserService.deactivate(inactive_user)
    create_invited_user(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/users',
        data={'status': UserStatus.INACTIVE},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == inactive_user.id


def test_list__status_active__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    inactive_user = create_test_user(
        account=account,
        email='test@test.test'
    )
    UserService.deactivate(inactive_user)
    create_invited_user(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/users',
        data={'status': UserStatus.ACTIVE},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == user.id


def test_list__status_invited__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    inactive_user = create_test_user(
        account=account,
        email='test@test.test'
    )
    UserService.deactivate(inactive_user)
    invited_user = create_invited_user(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/users',
        data={'status': UserStatus.INVITED},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == invited_user.id


def test_list__status_multiple_values__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account, last_name='z')
    inactive_user = create_test_user(
        account=account,
        email='test@test.test'
    )
    UserService.deactivate(inactive_user)
    invited_user = create_invited_user(user, last_name='x')
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/users?status={UserStatus.INVITED},{UserStatus.ACTIVE}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == invited_user.id
    assert response.data[1]['id'] == user.id


def test_list__type_user__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account, is_account_owner=True)
    create_test_guest(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/users',
        data={
            'type': UserType.USER
        }
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == user.id


def test_list__type_guest__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_user(
        account=account,
        is_account_owner=True,
        email='owner@test.test',
    )
    user = create_test_user(account=account)
    guest = create_test_guest(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/users',
        data={
            'type': UserType.GUEST
        }
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == guest.id


def test_list__type_multiple_values__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_user(
        account=account,
        is_account_owner=True,
        email='owner@test.test',
        last_name='owner'
    )
    user = create_test_user(account=account, last_name='user')
    guest = create_test_guest(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/users?type={UserType.GUEST}, {UserType.USER}'
        f'?ordering=last_name'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]['id'] == guest.id
    assert response.data[1]['id'] == owner.id
    assert response.data[2]['id'] == user.id


def test_list__type_invalid_value__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    undefined_type = 'undefined_type'

    # act
    response = api_client.get(
        f'/accounts/users?type={UserType.GUEST}, {undefined_type}',
    )

    # assert
    assert response.status_code == 400
    assert response.data[0] == MSG_GE_0001(undefined_type)


def test_list__ordering_by_status__ok(api_client):

    # arrange
    user = create_test_user()
    invited = create_invited_user(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        path='/accounts/users',
        data={'ordering': 'status'}
    )

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == user.id
    assert response.data[1]['id'] == invited.id
    assert response.data[1]['invite']['by_username'] == user.name


def test_list__ordering_by_status_desc_ok(api_client):

    # arrange
    user = create_test_user()
    invited = create_invited_user(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        path='/accounts/users',
        data={'ordering': '-status'}
    )

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == invited.id
    assert response.data[1]['id'] == user.id


def test_list__ordering_by_last_name__ok(api_client):

    # arrange
    user = create_test_user(last_name='Aaaaaa')
    invited = create_invited_user(user, last_name='Bbbbbbb')
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        path='/accounts/users',
        data={'ordering': 'last_name'}
    )

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == user.id
    assert response.data[1]['id'] == invited.id


def test_list__ordering_by_last_name_desc__ok(api_client):

    # arrange
    user = create_test_user(last_name='Aaaaaa')
    invited = create_invited_user(user, last_name='Bbbbbbb')
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        path='/accounts/users',
        data={'ordering': '-last_name'}
    )

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == invited.id
    assert response.data[1]['id'] == user.id


def test_list__ordering_multiple_values__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account, last_name='b')
    user.status = UserStatus.INVITED
    user.save()
    user2 = create_test_user(
        account=account,
        last_name='b',
        email='user2@test.test'
    )
    user2.status = UserStatus.ACTIVE
    user2.save()
    invited = create_invited_user(user, last_name='a')
    api_client.token_authenticate(user2)

    # act
    response = api_client.get(
        path='/accounts/users?ordering=last_name,status'
    )

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == invited.id
    assert response.data[1]['id'] == user2.id
    assert response.data[2]['id'] == user.id


def test_list__ordering_by_multiple_values_2__ok(api_client):

    # arrange
    user = create_test_user(
        first_name='A',
        last_name='C'
    )
    user_2 = create_test_user(
        account=user.account,
        first_name='A',
        last_name='B',
        email='t@t.t'
    )
    invited = create_invited_user(
        user=user,
        first_name='B',
        last_name='A'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        path='/accounts/users?ordering=first_name,last_name'
    )

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == user_2.id
    assert response.data[1]['id'] == user.id
    assert response.data[2]['id'] == invited.id


def test_list__invited_from_current_acc__correct_count(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_user(account=account, is_account_owner=True)
    user = create_invited_user(user=owner)
    another_acc_user = create_test_user(email='another@pneumatic.app')
    UserInvite.objects.create(
        email=another_acc_user.email,
        account=another_acc_user.account,
        invited_user=user,
    )

    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        path='/accounts/users',
        data={
            'ordering': 'first_name'
        }

    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == user.id
    assert response.data[0]['invite']['id'] == str(user.invite.id)


def test_list__inactive_users_from_another_acc_with_invite__ok(
    mocker,
    api_client,
):
    """
        Check:
         Inactive user from another acc has an invite to current account.
         Then he will be shown in a list.
         Inactive user in current account will be shown in a list.
    """
    account_owner = create_test_owner(last_name='z')
    inactive_invited_user = create_invited_user(
        user=account_owner,
        email='invited@pneumatic.app',
        last_name='x'
    )
    UserService.deactivate(inactive_invited_user)
    another_account_owner = create_test_owner(
        email='anotheracc@pneumatic.app',
    )
    another_account_inactive_user = create_invited_user(
        another_account_owner,
        email='inactive@pneumatic.app',
        last_name='y'
    )
    UserService.deactivate(another_account_inactive_user)
    UserInvite.objects.create(
        email=another_account_inactive_user.email,
        account=account_owner.account,
        invited_by=account_owner,
        invited_user=another_account_inactive_user,
    )

    mocker.patch(
        'pneumatic_backend.services.email.EmailService.'
        'send_user_deactivated_email'
    )
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get('/accounts/users')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]['id'] == inactive_invited_user.id
    assert response.data[1]['id'] == another_account_inactive_user.id
    assert response.data[2]['id'] == account_owner.id


def test_list__guest__ok(api_client):

    """ Request from authenticated guest by token """

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        account=account,
        email='owner@test.test',
        is_account_owner=True,
        last_name='a'
    )
    guest = create_test_guest(account=account, email='b@test.test')
    workflow = create_test_workflow(account_owner, tasks_count=1)
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
        path='/accounts/users',
        **{'X-Guest-Authorization': str_token}
    )

    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == guest.id
    assert response.data[0]['type'] == UserType.GUEST
    assert response.data[1]['id'] == account_owner.id
    assert response.data[1]['type'] == UserType.USER


def test_list__another_acc_users__not_found(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_user(
        account=account,
        is_account_owner=True,
        email='owner@test.test',
    )
    user = create_test_user(account=account)
    api_client.token_authenticate(user)

    another_account = create_test_account()
    create_test_user(
        account=another_account,
        is_account_owner=True,
        email='another-owner@test.test',
    )
    another_user = create_test_user(
        account=another_account,
        email='another@user.test'
    )

    create_invited_user(another_user)
    another_inactive_user = create_test_user(
        account=another_account,
        email='test@test.test',
    )
    UserService.deactivate(another_inactive_user)
    create_test_guest(account=another_account)

    # act
    response = api_client.get('/accounts/users')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == owner.id


@pytest.mark.parametrize('is_account_owner', (True, False))
def test_list__remove_transferred__new_account_ok(
    api_client,
    is_account_owner
):

    # arrange
    account_1 = create_test_account(name='transfer from')
    account_2 = create_test_account(
        name='transfer to',
        plan=BillingPlanType.PREMIUM
    )
    user_to_transfer = create_test_user(
        account=account_1,
        email='user_to_transfer@test.test',
        is_account_owner=is_account_owner
    )
    account_2_owner = create_test_user(
        account=account_2,
        is_account_owner=True,
        email='owner@test.test'
    )
    current_url = 'some_url'
    service = UserInviteService(
        request_user=account_2_owner,
        current_url=current_url
    )
    service.invite_user(
        email=user_to_transfer.email,
        invited_from=SourceType.EMAIL
    )
    account_2_new_user = account_2.users.get(email=user_to_transfer.email)
    UserService.deactivate(user_to_transfer)
    api_client.token_authenticate(account_2_owner)

    # act
    response = api_client.get('/accounts/users?ordering=status')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == account_2_owner.id
    assert response.data[1]['id'] == account_2_new_user.id
    assert response.data[1]['status'] == UserStatus.INVITED
    assert response.data[1]['type'] == UserType.USER


@pytest.mark.parametrize('is_account_owner', (True, False))
def test_list__remove_transferred__prev_account_ok(
    api_client,
    is_account_owner
):

    # arrange
    account_1 = create_test_account(name='transfer from')
    account_2 = create_test_account(
        name='transfer to',
        plan=BillingPlanType.PREMIUM
    )
    account_1_owner = create_test_user(
        account=account_1,
        is_account_owner=True,
        email='owner1@test.test'
    )
    user_to_transfer = create_test_user(
        account=account_1,
        email='user_to_transfer@test.test',
        is_account_owner=is_account_owner
    )
    account_2_owner = create_test_user(
        account=account_2,
        is_account_owner=True,
        email='owner@test.test'
    )
    current_url = 'some_url'
    service = UserInviteService(
        request_user=account_2_owner,
        current_url=current_url
    )
    service.invite_user(
        email=user_to_transfer.email,
        invited_from=SourceType.EMAIL
    )
    UserService.deactivate(user_to_transfer)
    api_client.token_authenticate(account_1_owner)

    # act
    response = api_client.get('/accounts/users?ordering=status')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['status'] == UserStatus.ACTIVE
    assert response.data[0]['id'] == account_1_owner.id
    assert response.data[1]['status'] == UserStatus.INACTIVE
    assert response.data[1]['id'] == user_to_transfer.id
    assert response.data[1]['type'] == UserType.USER
