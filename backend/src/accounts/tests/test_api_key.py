import pytest

from src.accounts.models import APIKey
from src.accounts.services.api_key import APIKeyService

pytestmark = pytest.mark.django_db


def test_generate_key__prefix__ok():

    # arrange
    pass

    # act
    key = APIKeyService.generate_key()

    # assert
    expected_prefix = APIKey.API_KEY_PREFIX
    assert key.startswith(expected_prefix)
    assert len(key) > len(expected_prefix)


def test_is_expired__no_expiry__false():

    # arrange
    api_key = APIKey(expires_at=None)

    # act
    result = api_key.is_expired

    # assert
    assert result is False
