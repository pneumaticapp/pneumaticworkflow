import pytest

from src.accounts.models import APIKey
from src.authentication.tokens import PneumaticToken
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_destroy_api_key__ok(
    mocker,
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    member = create_test_not_admin(
        account=owner.account,
        email='member@test.com',
    )
    cache_delete_mock = mocker.patch(
        'src.authentication.tokens'
        '.PneumaticToken.cache.delete',
    )
    raw_key = PneumaticToken.create(
        user=member,
        for_api_key=True,
    )
    api_key = APIKey.objects.create(
        user=member,
        name='To revoke',
        account_id=member.account_id,
        prefix=raw_key[:16],
        key_hash=APIKey.hash_key(raw_key),
        cache_token=PneumaticToken.encrypt(raw_key),
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.delete(
        f'/accounts/users/{member.id}/api-keys/{api_key.id}',
    )

    # assert
    assert response.status_code == 204
    api_key.refresh_from_db()
    assert api_key.is_active is False
    cache_delete_mock.assert_called_once_with(
        api_key.cache_token,
    )


def test_destroy_api_key__other_account__not_found(
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    other_user = create_test_owner(
        email='other@test.com',
    )
    api_key = APIKey.objects.create(
        user=other_user,
        name='Other account key',
        account_id=other_user.account_id,
        prefix='pn_live_other_',
        key_hash='hash_other',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.delete(
        f'/accounts/users/{other_user.id}/api-keys/{api_key.id}',
    )

    # assert
    assert response.status_code == 404


def test_destroy_api_key__already_revoked__not_found(
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    member = create_test_not_admin(
        account=owner.account,
        email='member@test.com',
    )
    api_key = APIKey.objects.create(
        user=member,
        name='Revoked',
        account_id=member.account_id,
        prefix='pn_live_revokd',
        key_hash='hash_revoked',
        is_active=False,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.delete(
        f'/accounts/users/{member.id}/api-keys/{api_key.id}',
    )

    # assert
    assert response.status_code == 404


def test_destroy_api_key__not_owner__forbidden(
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
    raw_key = PneumaticToken.create(
        user=member,
        for_api_key=True,
    )
    api_key = APIKey.objects.create(
        user=member,
        name='Member Key',
        account_id=member.account_id,
        prefix=raw_key[:16],
        key_hash=APIKey.hash_key(raw_key),
        cache_token=PneumaticToken.encrypt(raw_key),
    )
    api_client.token_authenticate(admin)

    # act
    response = api_client.delete(
        f'/accounts/users/{member.id}/api-keys/{api_key.id}',
    )

    # assert
    assert response.status_code == 403


def test_destroy_api_key__nonexistent_user__not_found(
    api_client,
    identify_mock,
):

    # arrange
    owner = create_test_owner()
    api_client.token_authenticate(owner)

    # act
    response = api_client.delete(
        '/accounts/users/999999/api-keys/1',
    )

    # assert
    assert response.status_code == 404
