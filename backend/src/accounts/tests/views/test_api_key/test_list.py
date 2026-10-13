import pytest
from datetime import timedelta

from django.utils import timezone

from src.accounts.models import APIKey
from src.authentication.tokens import PneumaticToken
from src.processes.tests.fixtures import (
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_list__valid_key__returned(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    raw_key = PneumaticToken.create(user, for_api_key=True)
    api_key = APIKey.objects.create(
        user=user,
        account=user.account,
        name='My Key',
        token=raw_key,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/api-keys')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data = response.data[0]
    assert data['id'] == api_key.id
    assert data['name'] == 'My Key'
    assert data['prefix'] == raw_key[:16]
    assert 'token' not in data
    assert 'key' not in data


def test_list__deactivated_key__excluded(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    APIKey.objects.create(
        user=user,
        account=user.account,
        name='Active',
        token='pn-active_key_xx',
        is_active=True,
    )
    APIKey.objects.create(
        user=user,
        account=user.account,
        name='Deactivated',
        token='pn-deactivated_k',
        is_active=False,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/api-keys')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['name'] == 'Active'


def test_list__other_user_key__excluded(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    other_user = create_test_not_admin(
        account=user.account, email='other@test.com',
    )
    APIKey.objects.create(
        user=user,
        account=user.account,
        name='My Key',
        token='pn-my_key_123456',
    )
    APIKey.objects.create(
        user=other_user,
        account=user.account,
        name='Other Key',
        token='pn-other_key_1234',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/api-keys')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['name'] == 'My Key'


def test_list__expired_key__included(api_client, identify_mock):
    """Expired but active keys should still appear in the list."""

    # arrange
    user = create_test_owner()
    APIKey.objects.create(
        user=user,
        account=user.account,
        name='Expired',
        token='pn-expired_key_12',
        expires_at=timezone.now() - timedelta(days=1),
        is_active=True,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/api-keys')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['name'] == 'Expired'


def test_list__deleted_key__excluded(api_client, identify_mock):
    """Deleted keys should not appear in the list."""

    # arrange
    user = create_test_owner()
    APIKey.objects.create(
        user=user,
        account=user.account,
        name='Deleted',
        token='pn-deleted_key_12',
        is_deleted=True,
    )
    APIKey.objects.create(
        user=user,
        account=user.account,
        name='Active',
        token='pn-active_key_34',
        is_deleted=False,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/api-keys')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['name'] == 'Active'
