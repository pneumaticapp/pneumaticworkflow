import hashlib
from datetime import timedelta

import pytest
from django.utils import timezone

from src.accounts.models import APIKey
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_hash_key__ok():
    # arrange
    raw_key = 'test_raw_key'
    expected_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    # act
    result = APIKey.hash_key(raw_key=raw_key)

    # assert
    assert result == expected_hash


def test_generate_key__starts_with_prefix__ok(settings):
    # arrange
    prefix = 'pn_live_'
    settings.API_KEY_PREFIX = prefix

    # act
    key = APIKey.generate_key()

    # assert
    assert isinstance(key, str)
    assert len(key) > 16
    assert key.startswith(prefix)


def test_generate_key__unique__ok():
    # arrange
    # (no setup required)

    # act
    key1 = APIKey.generate_key()
    key2 = APIKey.generate_key()

    # assert
    assert key1 != key2


def test_is_expired__no_expiry__false():
    # arrange
    api_key = APIKey(expires_at=None)

    # act
    result = api_key.is_expired

    # assert
    assert not result


def test_is_expired__future__false(mocker):
    # arrange
    mocked_now = timezone.now()
    mocker.patch('django.utils.timezone.now', return_value=mocked_now)
    api_key = APIKey(expires_at=mocked_now + timedelta(days=1))

    # act
    result = api_key.is_expired

    # assert
    assert not result


def test_is_expired__past__true(mocker):
    # arrange
    mocked_now = timezone.now()
    mocker.patch('django.utils.timezone.now', return_value=mocked_now)
    api_key = APIKey(expires_at=mocked_now - timedelta(days=1))

    # act
    result = api_key.is_expired

    # assert
    assert result


def test_active__filters_active__ok():
    # arrange
    user = create_test_owner()
    APIKey.objects.create(
        user=user,
        account=user.account,
        name='Active',
        prefix='pn_live_',
        key_hash='hash1',
        is_active=True,
    )
    APIKey.objects.create(
        user=user,
        account=user.account,
        name='Inactive',
        prefix='pn_live_',
        key_hash='hash2',
        is_active=False,
    )

    # act
    active_keys = APIKey.objects.active()

    # assert
    assert active_keys.count() == 1
    assert active_keys.first().name == 'Active'


def test_by_user__filters_by_user_id__ok():
    # arrange
    user1 = create_test_owner(email='u1@test.com')
    user2 = create_test_owner(email='u2@test.com')
    APIKey.objects.create(
        user=user1,
        account=user1.account,
        name='K1',
        prefix='pn_live_',
        key_hash='hash1',
        is_active=True,
    )
    APIKey.objects.create(
        user=user2,
        account=user2.account,
        name='K2',
        prefix='pn_live_',
        key_hash='hash2',
        is_active=True,
    )

    # act
    user1_keys = APIKey.objects.by_user(user_id=user1.id)

    # assert
    assert user1_keys.count() == 1
    assert user1_keys.first().user_id == user1.id


def test_not_expired__excludes_past__ok(mocker):
    # arrange
    mocked_now = timezone.now()
    mocker.patch('django.utils.timezone.now', return_value=mocked_now)
    user = create_test_owner()
    APIKey.objects.create(
        user=user,
        account=user.account,
        name='No expiry',
        prefix='pn_live_',
        key_hash='hash1',
        expires_at=None,
    )
    APIKey.objects.create(
        user=user,
        account=user.account,
        name='Future',
        prefix='pn_live_',
        key_hash='hash2',
        expires_at=mocked_now + timedelta(days=1),
    )
    APIKey.objects.create(
        user=user,
        account=user.account,
        name='Past',
        prefix='pn_live_',
        key_hash='hash3',
        expires_at=mocked_now - timedelta(days=1),
    )

    # act
    valid_keys = APIKey.objects.not_expired()

    # assert
    assert valid_keys.count() == 2
    assert valid_keys.filter(name='Past').exists() is False
