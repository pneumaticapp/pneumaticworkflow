import pytest

from src.accounts.models import APIKey
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_create__for_user__created(
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    member = create_test_not_admin(
        account=owner.account,
        email='member@test.com',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/accounts/users/{member.id}/api-keys',
        data={'name': 'Test Key for Member'},
    )

    # assert
    assert response.status_code == 201
    assert response.data['name'] == 'Test Key for Member'
    assert isinstance(response.data['token'], str)
    assert len(response.data['token']) > 16
    assert response.data['prefix'] == (
        response.data['token'][:16]
    )
    api_key = APIKey.objects.get(
        id=response.data['id'],
    )
    assert api_key.user_id == member.id
    assert api_key.account_id == owner.account_id


def test_create__auto_name__created(
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    member = create_test_not_admin(
        account=owner.account,
        email='member@test.com',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/accounts/users/{member.id}/api-keys',
        data={},
    )

    # assert
    assert response.status_code == 201
    assert response.data['name'] == 'API Key #1'


def test_create__for_admin__created(
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    admin = create_test_admin(
        account=owner.account,
        email='admin@test.com',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/accounts/users/{admin.id}/api-keys',
        data={'name': 'Admin Key'},
    )

    # assert
    assert response.status_code == 201
    api_key = APIKey.objects.get(
        id=response.data['id'],
    )
    assert api_key.user_id == admin.id


def test_create__other_account__not_found(
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    other_user = create_test_owner(
        email='other@test.com',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/accounts/users/{other_user.id}/api-keys',
        data={'name': 'Should fail'},
    )

    # assert
    assert response.status_code == 404


def test_create__nonexistent__not_found(
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users/999999/api-keys',
        data={'name': 'Should fail'},
    )

    # assert
    assert response.status_code == 404


def test_create__not_owner__forbidden(
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    member = create_test_not_admin(
        account=owner.account,
        email='member@test.com',
    )
    admin = create_test_admin(
        account=owner.account,
        email='admin@test.com',
    )
    api_client.token_authenticate(admin)

    # act
    response = api_client.post(
        f'/accounts/users/{member.id}/api-keys',
        data={'name': 'Admin try'},
    )

    # assert
    assert response.status_code == 403


def test_create__for_self__created(
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/accounts/users/{owner.id}/api-keys',
        data={'name': 'Self Key'},
    )

    # assert
    assert response.status_code == 201
    api_key = APIKey.objects.get(
        id=response.data['id'],
    )
    assert api_key.user_id == owner.id
