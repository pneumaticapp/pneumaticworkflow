import pytest

from src.accounts.models import APIKey
from src.authentication.tokens import PneumaticToken
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_destroy__valid_key__destroyed(mocker, api_client, identify_mock):

    # arrange
    user = create_test_owner()
    raw_key = PneumaticToken.create(
        user=user,
        for_api_key=True,
    )
    api_key = APIKey.objects.create(
        user=user,
        name='To revoke',
        account_id=user.account_id,
        token=raw_key,
    )
    api_client.token_authenticate(user)

    cache_delete_mock = mocker.patch(
        'src.accounts.services.api_key'
        '.PneumaticToken.cache.delete',
    )

    # act
    response = api_client.delete(
        f'/accounts/api-keys/{api_key.id}',
    )

    # assert
    assert response.status_code == 204
    api_key.refresh_from_db()
    assert api_key.is_active is False
    expected_cache_key = PneumaticToken.encrypt(raw_key)
    cache_delete_mock.assert_called_once_with(
        expected_cache_key,
    )


def test_destroy__other_user__not_found(
    api_client,
    identify_mock,
):

    # arrange
    user = create_test_owner()
    other_user = create_test_owner(
        email='other@test.com',
    )
    api_key = APIKey.objects.create(
        user=other_user,
        name='Other key',
        account_id=other_user.account_id,
        token='pn-other_user_key',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.delete(
        f'/accounts/api-keys/{api_key.id}',
    )

    # assert
    assert response.status_code == 404


def test_destroy__already_revoked__not_found(
    api_client,
    identify_mock,
):

    # arrange
    user = create_test_owner()
    api_key = APIKey.objects.create(
        user=user,
        name='Revoked',
        account_id=user.account_id,
        token='pn-revoked_key_x',
        is_active=False,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.delete(
        f'/accounts/api-keys/{api_key.id}',
    )

    # assert
    assert response.status_code == 404


def test_destroy__not_authenticated__unauthorized(
    api_client,
    identify_mock,
):

    # arrange
    user = create_test_owner()
    api_key = APIKey.objects.create(
        user=user,
        name='Key',
        account_id=user.account_id,
        token='pn-unauth_key_xx',
    )

    # act
    response = api_client.delete(
        f'/accounts/api-keys/{api_key.id}',
    )

    # assert
    assert response.status_code == 401
