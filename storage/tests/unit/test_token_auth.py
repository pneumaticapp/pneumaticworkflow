"""Tests for PneumaticToken auth and PBKDF2 hashing."""

from unittest.mock import AsyncMock

import pytest
import redis.asyncio as redis

from src.shared_kernel.auth.token_auth import (
    PneumaticToken,
    _compute_pbkdf2,
)

# --- PneumaticToken.data ---


@pytest.mark.asyncio
async def test_data__valid_token__return_data(
    mock_get_redis_client,
    mocker,
):

    # arrange
    token = 'test-token'
    expected_data = {'user_id': 1, 'account_id': 2}
    encrypted_token = 'encrypted-token-hash'
    encrypt_mock = mocker.patch(
        'src.shared_kernel.auth.token_auth'
        '.PneumaticToken.encrypt',
        return_value=encrypted_token,
    )
    mock_redis = AsyncMock()
    mock_redis.get.return_value = expected_data
    mock_get_redis_client.return_value = mock_redis

    # act
    result = await PneumaticToken.data(token)

    # assert
    assert result == expected_data
    encrypt_mock.assert_called_once_with(token)
    mock_redis.get.assert_called_once_with(encrypted_token)


@pytest.mark.asyncio
async def test_data__no_data_found__return_none(
    mock_get_redis_client,
    mocker,
):

    # arrange
    token = 'test-token'
    encrypted_token = 'encrypted-token-hash'
    encrypt_mock = mocker.patch(
        'src.shared_kernel.auth.token_auth'
        '.PneumaticToken.encrypt',
        return_value=encrypted_token,
    )
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_get_redis_client.return_value = mock_redis

    # act
    result = await PneumaticToken.data(token)

    # assert
    assert result is None
    encrypt_mock.assert_called_once_with(token)
    mock_redis.get.assert_called_once_with(encrypted_token)


@pytest.mark.asyncio
async def test_data__redis_error__raise_exception(
    mock_get_redis_client,
    mocker,
):

    # arrange
    token = 'test-token'
    encrypted_token = 'encrypted-token-hash'
    encrypt_mock = mocker.patch(
        'src.shared_kernel.auth.token_auth'
        '.PneumaticToken.encrypt',
        return_value=encrypted_token,
    )
    mock_redis = AsyncMock()
    mock_redis.get.side_effect = redis.RedisError(
        'Redis error',
    )
    mock_get_redis_client.return_value = mock_redis

    # act
    with pytest.raises(redis.RedisError):
        await PneumaticToken.data(token)

    # assert
    encrypt_mock.assert_called_once_with(token)
    mock_redis.get.assert_called_once_with(encrypted_token)


# --- _compute_pbkdf2 ---


def test_compute_pbkdf2__deterministic(clear_pbkdf2_cache):

    # act
    first = _compute_pbkdf2('token', 'salt', 1)
    second = _compute_pbkdf2('token', 'salt', 1)

    # assert
    assert first == second


def test_compute_pbkdf2__different_tokens(
    clear_pbkdf2_cache,
):

    # act
    hash1 = _compute_pbkdf2('token-a', 'salt', 1)
    hash2 = _compute_pbkdf2('token-b', 'salt', 1)

    # assert
    assert hash1 != hash2


def test_compute_pbkdf2__different_salts(
    clear_pbkdf2_cache,
):

    # act
    hash1 = _compute_pbkdf2('token', 'salt-a', 1)
    hash2 = _compute_pbkdf2('token', 'salt-b', 1)

    # assert
    assert hash1 != hash2


def test_compute_pbkdf2__returns_hex_string(
    clear_pbkdf2_cache,
):

    # act
    result = _compute_pbkdf2('token', 'salt', 1)

    # assert
    assert isinstance(result, str)
    assert len(result) == 64
    int(result, 16)  # must be valid hex


def test_compute_pbkdf2__cache_hit(clear_pbkdf2_cache):

    # act
    _compute_pbkdf2('tok', 'salt', 1)
    _compute_pbkdf2('tok', 'salt', 1)
    info = _compute_pbkdf2.cache_info()

    # assert
    assert info.hits == 1
    assert info.misses == 1


def test_compute_pbkdf2__cache_miss_diff_args(
    clear_pbkdf2_cache,
):

    # act
    _compute_pbkdf2('tok-a', 'salt', 1)
    _compute_pbkdf2('tok-b', 'salt', 1)
    info = _compute_pbkdf2.cache_info()

    # assert
    assert info.hits == 0
    assert info.misses == 2


# --- PneumaticToken.encrypt ---


@pytest.mark.asyncio
async def test_encrypt__returns_hex(
    clear_pbkdf2_cache,
    mock_get_settings,
):

    # arrange
    mock_get_settings.return_value.DJANGO_SECRET_KEY = 'secret'
    mock_get_settings.return_value.AUTH_TOKEN_ITERATIONS = 1

    # act
    result = await PneumaticToken.encrypt('my-token')

    # assert
    assert isinstance(result, str)
    assert len(result) == 64


@pytest.mark.asyncio
async def test_encrypt__no_to_thread(
    clear_pbkdf2_cache,
    mock_get_settings,
    mocker,
):

    # arrange
    mock_get_settings.return_value.DJANGO_SECRET_KEY = 'secret'
    mock_get_settings.return_value.AUTH_TOKEN_ITERATIONS = 1
    spy = mocker.patch(
        'src.shared_kernel.auth.token_auth.hashlib.pbkdf2_hmac',
        wraps=__import__('hashlib').pbkdf2_hmac,
    )

    # act
    await PneumaticToken.encrypt('my-token')

    # assert
    spy.assert_called_once_with(
        spy.call_args[0][0],
        spy.call_args[0][1],
        spy.call_args[0][2],
        spy.call_args[0][3],
    )


@pytest.mark.asyncio
async def test_encrypt__cached_on_repeat(
    clear_pbkdf2_cache,
    mock_get_settings,
):

    # arrange
    mock_get_settings.return_value.DJANGO_SECRET_KEY = 'secret'
    mock_get_settings.return_value.AUTH_TOKEN_ITERATIONS = 1

    # act
    first = await PneumaticToken.encrypt('cached-tok')
    second = await PneumaticToken.encrypt('cached-tok')

    # assert
    assert first == second
    info = _compute_pbkdf2.cache_info()
    assert info.hits >= 1


# --- Error handling ---


@pytest.mark.asyncio
async def test_data__value_error__returns_none(
    mock_get_redis_client,
    mocker,
):

    # arrange
    mocker.patch(
        'src.shared_kernel.auth.token_auth'
        '.PneumaticToken.encrypt',
        side_effect=ValueError('bad value'),
    )

    # act
    result = await PneumaticToken.data('bad-token')

    # assert
    assert result is None


@pytest.mark.asyncio
async def test_data__key_error__returns_none(
    mock_get_redis_client,
    mocker,
):

    # arrange
    mocker.patch(
        'src.shared_kernel.auth.token_auth'
        '.PneumaticToken.encrypt',
        side_effect=KeyError('missing'),
    )

    # act
    result = await PneumaticToken.data('bad-token')

    # assert
    assert result is None


@pytest.mark.asyncio
async def test_data__type_error__returns_none(
    mock_get_redis_client,
    mocker,
):

    # arrange
    mocker.patch(
        'src.shared_kernel.auth.token_auth'
        '.PneumaticToken.encrypt',
        side_effect=TypeError('wrong type'),
    )

    # act
    result = await PneumaticToken.data('bad-token')

    # assert
    assert result is None


@pytest.mark.asyncio
async def test_encrypt__empty_string__returns_hex(
    clear_pbkdf2_cache,
    mock_get_settings,
):

    # arrange
    mock_get_settings.return_value.DJANGO_SECRET_KEY = 'secret'
    mock_get_settings.return_value.AUTH_TOKEN_ITERATIONS = 1

    # act
    result = await PneumaticToken.encrypt('')

    # assert
    assert isinstance(result, str)
    assert len(result) == 64
