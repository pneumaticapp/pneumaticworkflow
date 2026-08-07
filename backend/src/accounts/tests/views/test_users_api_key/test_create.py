import pytest

from src.accounts.models import APIKey
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_api_key__create_for_user__ok(
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
        format='json',
    )

    # assert
    assert response.status_code == 201
    assert response.data['name'] == 'Test Key for Member'
    assert isinstance(response.data['key'], str)
    assert len(response.data['key']) > 16
    assert response.data['prefix'] == (
        response.data['key'][:16]
    )
    api_key = APIKey.objects.get(
        id=response.data['id'],
    )
    assert api_key.user_id == member.id
    assert api_key.account_id == owner.account_id


def test_api_key__create_auto_name__ok(
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
        format='json',
    )

    # assert
    assert response.status_code == 201
    assert response.data['name'] == 'API Key #1'


def test_api_key__create_for_admin__ok(
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
        format='json',
    )

    # assert
    assert response.status_code == 201
    api_key = APIKey.objects.get(
        id=response.data['id'],
    )
    assert api_key.user_id == admin.id


def test_api_key__create_other_account__not_found(
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
        format='json',
    )

    # assert
    assert response.status_code == 404


def test_api_key__create_nonexistent__not_found(
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
        format='json',
    )

    # assert
    assert response.status_code == 404


def test_api_key__create_not_owner__forbidden(
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
        format='json',
    )

    # assert
    assert response.status_code == 403


def test_api_key__create_for_self__ok(
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
        format='json',
    )

    # assert
    assert response.status_code == 201
    api_key = APIKey.objects.get(
        id=response.data['id'],
    )
    assert api_key.user_id == owner.id
