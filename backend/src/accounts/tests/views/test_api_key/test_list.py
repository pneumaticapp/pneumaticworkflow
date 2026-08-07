import pytest

from src.accounts.models import APIKey
from src.authentication.tokens import PneumaticToken
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_list__ok(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    raw_key = PneumaticToken.create(
        user=user,
        for_api_key=True,
    )
    api_key = APIKey.objects.create(
        user=user,
        name=user.get_full_name(),
        account_id=user.account_id,
        prefix=raw_key[:16],
        key_hash=APIKey.hash_key(raw_key),
        cache_token=PneumaticToken.encrypt(raw_key),
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/api-keys')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data = response.data[0]
    assert data['id'] == api_key.id
    assert data['name'] == api_key.name
    assert data['prefix'] == api_key.prefix
    assert 'key' not in data
    assert 'key_hash' not in data


def test_list__not_authenticated__unauthorized(
    api_client,
    identify_mock,
):

    # arrange

    # act
    response = api_client.get('/accounts/api-keys')

    # assert
    assert response.status_code == 401
