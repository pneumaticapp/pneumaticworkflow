import pytest

from src.accounts.models import APIKey
from src.accounts.services.api_key import APIKeyService
from src.processes.tests.fixtures import (
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_revoke__deactivates_key__ok(mocker):
    # arrange
    user = create_test_owner()
    cache_delete_mock = mocker.patch(
        'src.accounts.services.api_key.PneumaticToken.cache.delete',
    )
    api_key = APIKey.objects.create(
        user=user,
        account=user.account,
        name='Test',
        prefix='pn_live_',
        key_hash='hash',
        cache_token='cache_token_123',
    )

    # act
    service = APIKeyService(user=user, instance=api_key)
    service.revoke()

    # assert
    api_key.refresh_from_db()
    assert not api_key.is_active
    cache_delete_mock.assert_called_once_with('cache_token_123')


def test_revoke__no_cache_token__skip(mocker):
    # arrange
    user = create_test_owner()
    cache_delete_mock = mocker.patch(
        'src.accounts.services.api_key.PneumaticToken.cache.delete',
    )
    api_key = APIKey.objects.create(
        user=user,
        account=user.account,
        name='Test',
        prefix='pn_live_',
        key_hash='hash',
        cache_token='',
    )

    # act
    service = APIKeyService(user=user, instance=api_key)
    service.revoke()

    # assert
    api_key.refresh_from_db()
    assert not api_key.is_active
    cache_delete_mock.assert_not_called()


def test_create_for_user__account_owner__ok():
    # arrange
    owner = create_test_owner()
    member = create_test_not_admin(account=owner.account)
    service = APIKeyService(user=owner)

    # act
    api_key, raw_key = service.create_for_user(
        target_user=member,
        name='Member CI Key',
    )

    # assert
    assert api_key.user_id == member.id
    assert api_key.account_id == member.account_id
    assert api_key.name == 'Member CI Key'
    assert api_key.prefix == raw_key[:16]
    assert api_key.is_active is True
    assert len(raw_key) > 0


def test_create_for_user__auto_name__ok():
    # arrange
    owner = create_test_owner()
    member = create_test_not_admin(account=owner.account)
    service = APIKeyService(user=owner)

    # act
    api_key, _ = service.create_for_user(target_user=member)

    # assert
    assert api_key.name == 'API Key #1'
