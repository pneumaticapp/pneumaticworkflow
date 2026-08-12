"""Unit-tests for APIKeyAuthentication."""
from datetime import timedelta

import pytest
from django.utils import timezone

from src.accounts.models import APIKey
from src.accounts.services.api_key import APIKeyService
from src.authentication.services.api_key_auth import APIKeyAuthentication
from src.authentication.tokens import PneumaticToken
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_authenticate_credentials__ok__auth_returned():

    # arrange
    user = create_test_owner()
    raw_key = APIKeyService.generate_key()
    APIKey.objects.create(
        user=user, account=user.account, name='Test',
        token=raw_key,
    )
    auth_service = APIKeyAuthentication()

    # act
    result = auth_service.authenticate_credentials(raw_key)

    # assert
    assert result is not None
    auth_user, _auth_token = result
    assert auth_user.id == user.id


def test_authenticate_credentials__cache_miss__cache_populated():

    # arrange
    user = create_test_owner()
    raw_key = APIKeyService.generate_key()
    APIKey.objects.create(
        user=user, account=user.account, name='Test',
        token=raw_key,
    )
    auth_service = APIKeyAuthentication()

    # act
    result = auth_service.authenticate_credentials(raw_key)

    # assert
    assert result is not None
    cached = PneumaticToken.data(raw_key)
    assert cached is not None
    assert cached['user_id'] == user.id


def test_authenticate_credentials__wrong_prefix__none():

    # arrange
    auth_service = APIKeyAuthentication()

    # act
    result = auth_service.authenticate_credentials('some_random_token')

    # assert
    assert result is None


def test_authenticate_credentials__expired__none():

    # arrange
    user = create_test_owner()
    raw_key = APIKeyService.generate_key()
    APIKey.objects.create(
        user=user, account=user.account, name='Expired',
        token=raw_key,
        expires_at=timezone.now() - timedelta(days=1),
    )
    auth_service = APIKeyAuthentication()

    # act
    result = auth_service.authenticate_credentials(raw_key)

    # assert
    assert result is None


def test_authenticate_credentials__inactive__none():

    # arrange
    user = create_test_owner()
    raw_key = APIKeyService.generate_key()
    APIKey.objects.create(
        user=user, account=user.account, name='Inactive',
        token=raw_key,
        is_active=False,
    )
    auth_service = APIKeyAuthentication()

    # act
    result = auth_service.authenticate_credentials(raw_key)

    # assert
    assert result is None


def test_authenticate_credentials__bytes_token__ok():

    # arrange
    user = create_test_owner()
    raw_key = APIKeyService.generate_key()
    APIKey.objects.create(
        user=user, account=user.account, name='Test',
        token=raw_key,
    )
    auth_service = APIKeyAuthentication()

    # act
    result = auth_service.authenticate_credentials(raw_key.encode())

    # assert
    assert result is not None
    assert result[0].id == user.id


def test_authenticate_credentials__not_found__none():

    # arrange
    raw_key = f'{APIKey.API_KEY_PREFIX}nonexistent_key_abc'
    auth_service = APIKeyAuthentication()

    # act
    result = auth_service.authenticate_credentials(raw_key)

    # assert
    assert result is None


def test_authenticate_credentials__first_use__last_used_updated():

    # arrange
    user = create_test_owner()
    raw_key = APIKeyService.generate_key()
    apikey = APIKey.objects.create(
        user=user, account=user.account, name='Test',
        token=raw_key,
    )
    assert apikey.last_used_at is None
    auth_service = APIKeyAuthentication()

    # act
    auth_service.authenticate_credentials(raw_key)

    # assert
    apikey.refresh_from_db()
    assert apikey.last_used_at is not None


def test_authenticate_credentials__cache_hit__ok(django_assert_num_queries):

    # arrange
    user = create_test_owner()
    raw_key = APIKeyService.generate_key()

    # Pre-populate cache, bypassing DB
    PneumaticToken.create(
        user=user, for_api_key=True, token=raw_key,
    )
    auth_service = APIKeyAuthentication()

    # act
    # 1 query for User.objects.get(pk=user.id), 0 for APIKey
    with django_assert_num_queries(1):
        result = auth_service.authenticate_credentials(raw_key)

    # assert
    assert result is not None
    assert result[0].id == user.id
