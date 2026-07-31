import hashlib
from datetime import timedelta

import pytest
from django.utils import timezone

from src.accounts.models import APIKey
from src.processes.tests.fixtures import create_test_user


pytestmark = pytest.mark.django_db


def test_hash_key__ok():
    # arrange
    raw_key = 'test_raw_key'
    expected_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    # act
    result = APIKey.hash_key(raw_key)

    # assert
    assert result == expected_hash


def test_generate_key__starts_with_prefix__ok():
    # act
    key = APIKey.generate_key()

    # assert
    assert key.startswith('pn_live_')
    assert len(key) > len('pn_live_')


def test_generate_key__unique__ok():
    # act
    key1 = APIKey.generate_key()
    key2 = APIKey.generate_key()

    # assert
    assert key1 != key2


def test_is_expired__no_expiry__false():
    # arrange
    api_key = APIKey(expires_at=None)

    # act & assert
    assert not api_key.is_expired


def test_is_expired__future__false():
    # arrange
    api_key = APIKey(expires_at=timezone.now() + timedelta(days=1))

    # act & assert
    assert not api_key.is_expired


def test_is_expired__past__true():
    # arrange
    api_key = APIKey(expires_at=timezone.now() - timedelta(days=1))

    # act & assert
    assert api_key.is_expired


def test_revoke__deactivates_key__ok(mocker):
    # arrange
    user = create_test_user()
    cache_delete_mock = mocker.patch(
        'src.authentication.tokens.PneumaticToken.cache.delete',
    )
    api_key = APIKey.objects.create(
        user=user,
        account=user.account,
        name='Test',
        prefix='pn_live_',
        key_hash='hash',
        cache_token='cache_token_123',
    )
    assert api_key.is_active

    # act
    api_key.revoke()

    # assert
    api_key.refresh_from_db()
    assert not api_key.is_active
    cache_delete_mock.assert_called_once_with('cache_token_123')


def test_revoke__no_cache_token__skip(mocker):
    # arrange
    user = create_test_user()
    cache_delete_mock = mocker.patch(
        'src.authentication.tokens.PneumaticToken.cache.delete',
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
    api_key.revoke()

    # assert
    api_key.refresh_from_db()
    assert not api_key.is_active
    cache_delete_mock.assert_not_called()


def test_active__filters_active__ok():
    # arrange
    user = create_test_user()
    APIKey.objects.create(
        user=user, account=user.account, name='Active',
        prefix='pn_live_', key_hash='hash1', is_active=True,
    )
    APIKey.objects.create(
        user=user, account=user.account, name='Inactive',
        prefix='pn_live_', key_hash='hash2', is_active=False,
    )

    # act
    active_keys = APIKey.objects.active()

    # assert
    assert active_keys.count() == 1
    assert active_keys.first().name == 'Active'


def test_by_user__filters_by_user_id__ok():
    # arrange
    user1 = create_test_user(email='u1@test.com')
    user2 = create_test_user(email='u2@test.com')
    APIKey.objects.create(
        user=user1, account=user1.account, name='K1',
        prefix='pn_live_', key_hash='hash1', is_active=True,
    )
    APIKey.objects.create(
        user=user2, account=user2.account, name='K2',
        prefix='pn_live_', key_hash='hash2', is_active=True,
    )

    # act
    user1_keys = APIKey.objects.by_user(user1.id)

    # assert
    assert user1_keys.count() == 1
    assert user1_keys.first().user_id == user1.id


def test_not_expired__excludes_past__ok():
    # arrange
    user = create_test_user()
    APIKey.objects.create(
        user=user, account=user.account, name='No expiry',
        prefix='pn_live_', key_hash='hash1', expires_at=None,
    )
    APIKey.objects.create(
        user=user, account=user.account, name='Future',
        prefix='pn_live_', key_hash='hash2',
        expires_at=timezone.now() + timedelta(days=1),
    )
    APIKey.objects.create(
        user=user, account=user.account, name='Past',
        prefix='pn_live_', key_hash='hash3',
        expires_at=timezone.now() - timedelta(days=1),
    )

    # act
    valid_keys = APIKey.objects.not_expired()

    # assert
    assert valid_keys.count() == 2
    names = set(valid_keys.values_list('name', flat=True))
    assert 'Past' not in names
