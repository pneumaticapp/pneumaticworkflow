import pytest

from src.accounts.enums import (
    UserDateFormat,
    UserStatus,
    UserType,
)
from src.accounts.services.user import UserService
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.generics.messages import MSG_GE_0001
from src.processes.enums import OwnerType
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.raw_performer import RawPerformerTemplate
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_user,
    create_test_workflow,
)
from src.utils.dates import date_format

pytestmark = pytest.mark.django_db


def test_privileges__response_format__ok(api_client):
    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    group = create_test_group(account, users=[user])
    template = create_test_template(user=user, tasks_count=1)
    TemplateOwner.objects.all().delete()
    owner = TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.USER,
        user_id=user.id,
    )
    task = TaskTemplate.objects.get(template=template)
    performer = RawPerformerTemplate.objects.get(user=user)

    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/users/privileges')

    # assert
    assert response.status_code == 200
    data = response.data[0]
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
    assert data['is_account_owner'] == user.is_account_owner
    assert data['language'] == user.language
    assert data['timezone'] == user.timezone
    assert data['date_fmt'] == UserDateFormat.API_USA_12
    assert data['date_fdw'] == user.date_fdw
    assert data['invite'] is None
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

    assert len(data['groups']) == 1
    assert data['groups'][0]['id'] == group.id
    assert data['groups'][0]['name'] == group.name

    assert len(data['templates']) == 1
    data_template = data['templates'][0]
    assert data_template['id'] == template.id
    assert data_template['name'] == template.name
    assert data_template['is_active'] == template.is_active
    assert data_template['is_public'] == template.is_public

    assert len(data_template['owners']) == 1
    data_owner = data_template['owners'][0]
    assert data_owner['api_name'] == owner.api_name
    assert data_owner['type'] == owner.type
    assert data_owner['source_id'] == str(owner.user_id)

    assert len(data_template['tasks']) == 1
    data_tasks = data_template['tasks'][0]
    assert data_tasks['number'] == task.number
    assert data_tasks['api_name'] == task.api_name
    assert data_tasks['name'] == task.name

    assert len(data_tasks['raw_performers']) == 1
    data_raw_performers = data_tasks['raw_performers'][0]
    assert data_raw_performers['api_name'] == performer.api_name
    assert data_raw_performers['type'] == performer.type
    assert data_raw_performers['source_id'] == str(performer.user_id)
    assert data_raw_performers['label'] == performer.user.name_by_status


def test_privileges__pagination__ok(api_client):
    # arrange
    owner = create_test_owner()
    create_test_user(account=owner.account, email='igube1@ongi.tu')
    user = create_test_user(account=owner.account, email='igube2@ongi.tu')
    create_test_user(account=owner.account, email='igube3@ongi.tu')
    create_test_user(account=owner.account, email='igube4@ongi.tu')
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        '/accounts/users/privileges',
        data={
            'limit': 1,
            'offset': 2,
        },
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 5
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == user.id


def test_privileges__not_auth__permission_denied(api_client):
    # act
    response = api_client.get('/accounts/users/privileges')

    # assert
    assert response.status_code == 401


def test_privileges__guest__permission_denied(api_client):
    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    guest = create_test_guest(account=user.account)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=user.account.id,
    )

    # act
    response = api_client.get(
        path='/accounts/users/privileges',
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 403


def test_privileges__public_token__permission_denied(api_client):
    # arrange
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        is_public=True,
    )
    auth_header_value = f'Token {template.public_id}'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/users/privileges',
        **{'X-Public-Authorization': auth_header_value},
    )

    # assert
    assert response.status_code == 403


def test_privileges__not_admin__permission_denied(api_client):
    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/users/privileges')

    # assert
    assert response.status_code == 403


def test_privileges__admin__permission_denied(api_client):
    # arrange
    account = create_test_account()
    user = create_test_admin(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/users/privileges')

    # assert
    assert response.status_code == 403


def test_privileges__account_owner_from_another_acc__not_show(api_client):
    # arrange
    create_test_user()
    owner_another_account = create_test_owner(email='test@bou.tr')
    api_client.token_authenticate(owner_another_account)

    # act
    response = api_client.get('/accounts/users/privileges')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1


def test_privileges__filter_group__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    another_user = create_test_user(
        account=account,
        email='test@test.test',
    )
    create_test_user(
        account=account,
        email='additional@test.test',
    )
    group = create_test_group(
        account=account,
        users=[user, another_user],
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/users/privileges?groups={group.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == user.id
    assert response.data[1]['id'] == another_user.id


def test_privileges__group_multiple_values__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account, first_name='1')
    another_user = create_test_user(
        account=account,
        first_name='2',
        email='test@test.test',
    )
    create_test_user(
        account=account,
        email='additional@test.test',
    )
    group_1 = create_test_group(account=account, users=[another_user])
    group_2 = create_test_group(account=account, name='group 2', users=[user])
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/users/privileges?groups={group_1.id},{group_2.id}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == user.id
    assert response.data[1]['id'] == another_user.id


def test_privileges__status_inactive__ok(api_client):

    # arrange
    user = create_test_owner()
    inactive_user = create_test_user(
        account=user.account,
        email='test@test.test',
    )

    UserService.deactivate(inactive_user)
    create_invited_user(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/users/privileges',
        data={'status': UserStatus.INACTIVE},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == inactive_user.id


def test_privileges__status_active__ok(api_client):

    # arrange
    user = create_test_owner()
    inactive_user = create_test_user(
        account=user.account,
        email='test@test.test',
    )
    UserService.deactivate(inactive_user)
    create_invited_user(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/users/privileges',
        data={'status': UserStatus.ACTIVE},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == user.id


def test_privileges__status_invited__ok(api_client):

    # arrange
    user = create_test_owner()
    inactive_user = create_test_user(
        account=user.account,
        email='test@test.test',
    )
    UserService.deactivate(inactive_user)
    invited_user = create_invited_user(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/users/privileges',
        data={'status': UserStatus.INVITED},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == invited_user.id


def test_privileges__status_multiple_values__ok(api_client):

    # arrange
    user = create_test_owner(last_name='z')
    inactive_user = create_test_user(
        account=user.account,
        email='test@test.test',
    )
    UserService.deactivate(inactive_user)
    invited_user = create_invited_user(user, last_name='x')
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/users/privileges'
        f'?status={UserStatus.INVITED},{UserStatus.ACTIVE}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == invited_user.id
    assert response.data[1]['id'] == user.id


def test_privileges__type_user__ok(api_client):

    # arrange
    user = create_test_owner()
    create_test_guest(account=user.account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/users/privileges',
        data={
            'type': UserType.USER,
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == user.id


def test_privileges__type_guest__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(
        account=account,
        email='owner@test.test',
    )
    create_test_user(
        account=account,
        is_account_owner=False,
    )
    guest = create_test_guest(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/users/privileges',
        data={
            'type': UserType.GUEST,
        },
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == guest.id


def test_privileges__type_multiple_values__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(
        account=account,
        email='owner@test.test',
    )
    user = create_test_user(
        account=account,
        is_account_owner=False,
    )
    guest = create_test_guest(account=account)
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        f'/accounts/users/privileges?type={UserType.GUEST}, {UserType.USER}'
        f'?ordering=last_name',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]['id'] == guest.id
    assert response.data[1]['id'] == owner.id
    assert response.data[2]['id'] == user.id


def test_privileges__type_invalid_value__ok(api_client):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    undefined_type = 'undefined_type'

    # act
    response = api_client.get(
        f'/accounts/users/privileges?type={UserType.GUEST}, {undefined_type}',
    )

    # assert
    assert response.status_code == 400
    assert response.data[0] == MSG_GE_0001(undefined_type)


def test_privileges__ordering_by_status__ok(api_client):

    # arrange
    user = create_test_owner()
    invited = create_invited_user(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        path='/accounts/users/privileges',
        data={'ordering': 'status'},
    )

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == user.id
    assert response.data[1]['id'] == invited.id
    assert response.data[1]['invite']['by_username'] == user.name


def test_privileges__ordering_by_status_desc_ok(api_client):

    # arrange
    user = create_test_owner()
    invited = create_invited_user(user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        path='/accounts/users/privileges',
        data={'ordering': '-status'},
    )

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == invited.id
    assert response.data[1]['id'] == user.id


def test_privileges__ordering_by_last_name__ok(api_client):

    # arrange
    user = create_test_owner(last_name='Aaaaaa')
    invited = create_invited_user(user, last_name='Bbbbbbb')
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        path='/accounts/users/privileges',
        data={'ordering': 'last_name'},
    )

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == user.id
    assert response.data[1]['id'] == invited.id


def test_privileges__ordering_by_last_name_desc__ok(api_client):

    # arrange
    user = create_test_owner(last_name='Aaaaaa')
    invited = create_invited_user(user, last_name='Bbbbbbb')
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        path='/accounts/users/privileges',
        data={'ordering': '-last_name'},
    )

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == invited.id
    assert response.data[1]['id'] == user.id


def test_privileges__ordering_multiple_values__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account, last_name='b')
    user.status = UserStatus.INVITED
    user.save()
    user2 = create_test_owner(
        account=account,
        last_name='b',
        email='user2@test.test',
    )
    user2.status = UserStatus.ACTIVE
    user2.save()
    invited = create_invited_user(user, last_name='a')
    api_client.token_authenticate(user2)

    # act
    response = api_client.get(
        path='/accounts/users/privileges?ordering=last_name,status',
    )

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == invited.id
    assert response.data[1]['id'] == user2.id
    assert response.data[2]['id'] == user.id


def test_privileges__ordering_by_multiple_values_2__ok(api_client):

    # arrange
    user = create_test_owner(
        first_name='A',
        last_name='C',
    )
    user_2 = create_test_user(
        account=user.account,
        first_name='A',
        last_name='B',
        email='t@t.t',
    )
    invited = create_invited_user(
        user=user,
        first_name='B',
        last_name='A',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        path='/accounts/users/privileges?ordering=first_name,last_name',
    )

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == user_2.id
    assert response.data[1]['id'] == user.id
    assert response.data[2]['id'] == invited.id
