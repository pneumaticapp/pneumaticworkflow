"""Contract checks on real HTTP exchanges, with no mocked response payloads."""

import pytest

from src.processes.tests.fixtures import (
    create_test_group,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('limit', [None, 1])
@pytest.mark.parametrize('path', [
    '/accounts/users', '/accounts/groups', '/ai/vendors',
    '/workflows', '/v3/tasks',
])
def test_lists__real_objects__match_contract(
    contract_api_client, path, limit,
) -> None:
    # arrange
    owner = create_test_owner()
    create_test_group(owner.account, users=[owner])
    create_test_workflow(owner)
    contract_api_client.token_authenticate(owner)

    # act
    response = contract_api_client.get(
        path, data={} if limit is None else {'limit': limit},
    )

    # assert
    assert response.status_code == 200
    data = response.json()
    assert data['results'] if isinstance(data, dict) else data


def test_profile__real_user__matches_contract(contract_api_client) -> None:
    # arrange
    owner = create_test_owner()
    contract_api_client.token_authenticate(owner)

    # act
    response = contract_api_client.get('/accounts/user')

    # assert
    assert response.status_code == 200
    assert response.json()['id'] == owner.id


def test_key__create_and_revoke__match_contract(contract_api_client) -> None:
    # arrange
    owner = create_test_owner()
    contract_api_client.token_authenticate(owner)

    # act
    created = contract_api_client.post(
        '/accounts/api-keys', data={'name': 'Contract key'}, format='json',
    )
    revoked = contract_api_client.delete(
        f"/accounts/api-keys/{created.json()['id']}",
    )

    # assert
    assert created.status_code == 201
    assert revoked.status_code == 204
    assert not revoked.content


def test_profile__unauthenticated__error_matches_contract(
    contract_api_client,
) -> None:
    # act
    response = contract_api_client.get('/accounts/user')

    # assert
    assert response.status_code == 401


@pytest.mark.parametrize('limit', [None, 1])
def test_templates__real_list__matches_contract(
    contract_api_client, limit,
) -> None:
    # arrange
    owner = create_test_owner()
    create_test_workflow(owner)
    contract_api_client.token_authenticate(owner)

    # act
    response = contract_api_client.get(
        '/templates', data={} if limit is None else {'limit': limit},
    )

    # assert
    assert response.status_code == 200


@pytest.mark.parametrize('limit', [None, 1])
@pytest.mark.parametrize('user_scoped', [False, True])
def test_key__real_list__matches_contract(
    contract_api_client, limit, user_scoped,
) -> None:
    # arrange
    owner = create_test_owner()
    contract_api_client.token_authenticate(owner)
    created = contract_api_client.post(
        '/accounts/api-keys', data={'name': 'Contract key'}, format='json',
    )
    assert created.status_code == 201

    # act
    path = (
        f'/accounts/users/{owner.id}/api-keys' if user_scoped
        else '/accounts/api-keys'
    )
    response = contract_api_client.get(
        path, data={} if limit is None else {'limit': limit},
    )

    # assert
    assert response.status_code == 200
    data = response.json()
    keys = data['results'] if isinstance(data, dict) else data
    assert len(keys) == 1
    assert 'token' not in keys[0]
    assert 'token' in created.json()


def test_group__real_create__matches_contract(contract_api_client) -> None:
    # arrange
    owner = create_test_owner()
    contract_api_client.token_authenticate(owner)

    # act
    response = contract_api_client.post(
        '/accounts/groups',
        data={'name': 'Contract group', 'photo': None}, format='json',
    )

    # assert
    assert response.status_code == 200
    assert response.json() == {'name': 'Contract group', 'photo': ''}
