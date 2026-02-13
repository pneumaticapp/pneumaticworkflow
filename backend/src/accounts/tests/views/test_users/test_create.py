import pytest

from src.accounts.enums import (
    UserDateFormat, UserFirstDayWeek,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_create__ok(api_client):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    email = 'some@email.com'
    request_data = {
        'email': email,
        'first_name': 'First',
        'last_name': 'Last',
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
    }

    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        request_data,
    )

    # assert
    assert response.status_code == 200
    data = response.data
    user = account.users.get(email=email)
    assert data['id'] == user.id
    assert data['email'] == user.email
    assert data['phone'] == user.phone
    assert data['photo'] == user.photo
    assert data['first_name'] == user.first_name
    assert data['last_name'] == user.last_name
    assert data['type'] == user.type
    assert data['date_joined_tsp'] == user.date_joined.timestamp()
    assert data['is_admin'] == user.is_admin
    assert data['is_account_owner'] == user.is_account_owner
    assert data['language'] == user.language
    assert data['timezone'] == user.timezone
    assert data['date_fmt'] == UserDateFormat.API_USA_24
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
