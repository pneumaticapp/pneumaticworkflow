import pytest
from src.accounts.enums import (
    UserDateFormat,
)
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_group,
)


pytestmark = pytest.mark.django_db
date_format = '%Y-%m-%dT%H:%M:%S.%fZ'


def test_retrieve__ok(api_client):

    # arrange
    user = create_test_user()
    group_1 = create_test_group(
        user.account,
        name='group_1',
        users=[user]
    )
    group_2 = create_test_group(
        user.account,
        name='group_2',
        users=[user]
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/accounts/users/{user.id}')

    # assert
    assert response.status_code == 200
    data = response.data
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


def test_retrieve__not_authenticated__unauthorized(api_client):

    # arrange
    user = create_test_user()

    # act
    response = api_client.get(f'/accounts/users/{user.id}')

    # assert
    assert response.status_code == 401
