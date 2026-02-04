import pytest
from src.accounts.enums import (
    UserDateFormat, UserFirstDayWeek,
)
from src.accounts.services.user import UserService
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner, create_test_group, create_test_not_admin,
)

pytestmark = pytest.mark.django_db


def test_create__all_fields__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    group = create_test_group(account=account, users=[owner])
    email = 'some@email.com'
    request_data = {
        'email': email,
        'first_name': 'First',
        'last_name': 'Last',
        'password': 'some password',
        'is_admin': False,
        'photo': 'https://my.lovely.photo.jpg',
        'phone': '79999999990',
        'is_tasks_digest_subscriber': False,
        'is_digest_subscriber': False,
        'is_comments_mentions_subscriber': False,
        'is_new_tasks_subscriber': False,
        'is_complete_tasks_subscriber': False,
        'is_newsletters_subscriber': False,
        'is_special_offers_subscriber': False,
        'language': 'en',
        'timezone': 'America/Anchorage',
        'date_fmt': UserDateFormat.API_USA_24,
        'date_fdw': UserFirstDayWeek.THURSDAY,
        'groups': [group.id],
    }
    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.accounts.services.user.UserService.create',
        return_value=user,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        request_data,
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(**{
        'account': account,
        'email': email,
        'first_name': 'First',
        'last_name': 'Last',
        'raw_password': 'some password',
        'is_admin': False,
        'photo': 'https://my.lovely.photo.jpg',
        'phone': '79999999990',
        'is_tasks_digest_subscriber': False,
        'is_digest_subscriber': False,
        'is_comments_mentions_subscriber': False,
        'is_new_tasks_subscriber': False,
        'is_complete_tasks_subscriber': False,
        'is_newsletters_subscriber': False,
        'is_special_offers_subscriber': False,
        'language': 'en',
        'timezone': 'America/Anchorage',
        'date_fmt': UserDateFormat.PY_USA_24,
        'date_fdw': UserFirstDayWeek.THURSDAY,
        'user_groups': [group.id],
    })
    data = response.data
    assert data['id'] == user.id
    assert data['email'] == user.email
    assert data['phone'] == user.phone
    assert data['photo'] == user.photo
    assert data['first_name'] == user.first_name
    assert data['last_name'] == user.last_name
    assert 'password' not in data
    assert 'raw_password' not in data
    assert data['type'] == user.type
    assert data['date_joined_tsp'] == user.date_joined.timestamp()
    assert data['is_admin'] == user.is_admin
    assert data['is_account_owner'] == user.is_account_owner
    assert data['language'] == user.language
    assert data['timezone'] == user.timezone
    assert data['date_fmt'] == UserDateFormat.API_USA_12
    assert data['date_fdw'] == user.date_fdw
    assert data['invite'] is None
    assert data['groups'] == []
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
