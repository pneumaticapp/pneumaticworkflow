"""Unit-tests for PneumaticTokenAuthentication."""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from src.accounts.models import APIKey
from src.authentication.services.user_auth import PneumaticTokenAuthentication
from src.authentication.tokens import PneumaticToken
from src.processes.tests.fixtures import create_test_owner

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "cache_return, extra_kwargs, expect_none, as_bytes",
    [
        (None, {}, False, True),
        (None, {}, False, False),
        ({"for_api_key": True}, {}, False, True),
        (None, {"expires_at": timezone.now() - timedelta(days=1)}, True, True),
        (None, {"is_active": False}, True, True),
    ],
)
def test_authenticate_credentials__ok__auth_tuple(
    mocker,
    cache_return,
    extra_kwargs,
    expect_none,
    as_bytes,
):
    """Validate PneumaticTokenAuthentication behaviour for various states."""
    # arrange
    user = create_test_owner()
    raw_key = PneumaticToken.create(user, for_api_key=True)
    defaults = {
        "prefix": raw_key[:16],
        "key_hash": APIKey.hash_key(raw_key),
    }
    defaults.update(extra_kwargs)
    APIKey.objects.create(
        user=user, account=user.account, name='Test', **defaults,
    )

    if cache_return is not None:
        cache_return['user_id'] = user.id
        cache_return['is_superuser'] = False
        cache_return['token'] = PneumaticToken.encrypt(raw_key)

    token_data_mock = mocker.patch(
        'src.authentication.tokens.PneumaticToken.data',
        return_value=cache_return,
    )

    auth_service = PneumaticTokenAuthentication()
    token_to_pass = raw_key.encode() if as_bytes else raw_key

    # act
    result = auth_service.authenticate_credentials(token_to_pass)

    # assert
    if expect_none:
        assert result is None
    else:
        assert result is not None
        auth_user, auth_token = result
        assert auth_user.id == user.id
        assert auth_token.key == raw_key

    token_data_mock.assert_called_once_with(raw_key)


def test_authenticate_credentials__not_found__none(mocker):
    """Test when no APIKey exists for the given token."""
    # arrange
    user = create_test_owner()
    raw_key = PneumaticToken.create(user, for_api_key=True)

    token_data_mock = mocker.patch(
        'src.authentication.tokens.PneumaticToken.data',
        return_value=None,
    )
    auth_service = PneumaticTokenAuthentication()

    # act
    result = auth_service.authenticate_credentials(raw_key.encode())

    # assert
    assert result is None
    token_data_mock.assert_called_once_with(raw_key)
