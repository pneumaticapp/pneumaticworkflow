import pytest

from src.accounts.models import APIKey
from src.authentication.tokens import PneumaticToken
from src.processes.tests.fixtures import (
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_list__valid_user__returned(
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    member = create_test_not_admin(
        account=owner.account,
        email='member@test.com',
    )
    raw_key = PneumaticToken.create(
        user=member,
        for_api_key=True,
    )
    api_key = APIKey.objects.create(
        user=member,
        name='Member Key',
        account_id=member.account_id,
        token=raw_key,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        f'/accounts/users/{member.id}/api-keys',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data = response.data[0]
    assert data['id'] == api_key.id
    assert data['name'] == 'Member Key'
    assert 'key' not in data
    assert 'token' not in data


def test_list__empty__returned(
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
    response = api_client.get(
        f'/accounts/users/{member.id}/api-keys',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__excludes_revoked__returned(
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    member = create_test_not_admin(
        account=owner.account,
        email='member@test.com',
    )
    APIKey.objects.create(
        user=member,
        name='Active',
        account_id=member.account_id,
        token='pn-active_key_xx',
        is_active=True,
    )
    APIKey.objects.create(
        user=member,
        name='Revoked',
        account_id=member.account_id,
        token='pn-revoked_key_y',
        is_active=False,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        f'/accounts/users/{member.id}/api-keys',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['name'] == 'Active'


def test_list__deleted_key__excluded(
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    member = create_test_not_admin(
        account=owner.account,
        email='member@test.com',
    )
    APIKey.objects.create(
        user=member,
        name='Deleted',
        account_id=member.account_id,
        token='pn-deleted_key_12',
        is_deleted=True,
    )
    APIKey.objects.create(
        user=member,
        name='Active',
        account_id=member.account_id,
        token='pn-active_key_34',
        is_deleted=False,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        f'/accounts/users/{member.id}/api-keys',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['name'] == 'Active'
