"""Tests for RedisAuthClient and safe pickle deserialization."""

import os
import pickle
import subprocess
from unittest.mock import AsyncMock

import pytest
import redis.asyncio as redis

from src.shared_kernel.auth.redis_client import (
    RedisAuthClient,
    _safe_loads,
    _validate_auth_data,
    close_redis_client,
    get_redis_client,
)
from src.shared_kernel.exceptions import (
    RedisConnectionError,
    RedisOperationError,
)

# --- _safe_loads ---


def test_safe_loads__valid_dict__return_dict():

    # arrange
    data = {'user_id': 1, 'account_id': 2}

    # act
    result = _safe_loads(pickle.dumps(data))

    # assert
    assert result == data


def test_safe_loads__valid_list__return_list():

    # arrange
    data = ['token_hex_1', 'token_hex_2']

    # act
    result = _safe_loads(pickle.dumps(data))

    # assert
    assert result == data


def test_safe_loads__valid_nested__return_nested():

    # arrange
    data = {
        'user_id': 1,
        'account_id': 2,
        'user_agent': 'Mozilla/5.0',
        'user_ip': None,
        'for_api_key': False,
        'is_superuser': False,
    }

    # act
    result = _safe_loads(pickle.dumps(data))

    # assert
    assert result == data


def test_safe_loads__os_system__raise_error():

    # arrange
    payload = (
        b"\x80\x04\x95\x1e\x00\x00\x00\x00\x00\x00\x00"
        b"\x8c\x05posix\x8c\x06system\x93"
        b"\x8c\x0becho pwned\x85R."
    )

    # act
    with pytest.raises(
        pickle.UnpicklingError, match='Unsafe class',
    ):
        _safe_loads(payload)


def test_safe_loads__subprocess__raise_error():

    # arrange
    class Exploit:
        def __reduce__(self):
            return (subprocess.call, (['echo', 'pwned'],))

    payload = pickle.dumps(Exploit())

    # act
    with pytest.raises(
        pickle.UnpicklingError, match='Unsafe class',
    ):
        _safe_loads(payload)


def test_safe_loads__eval__raise_error():

    # arrange
    class EvalExploit:
        def __reduce__(self):
            return (eval, ('1+1',))

    payload = pickle.dumps(EvalExploit())

    # act
    with pytest.raises(
        pickle.UnpicklingError, match='Unsafe class',
    ):
        _safe_loads(payload)


def test_safe_loads__exec__raise_error():

    # arrange
    class ExecExploit:
        def __reduce__(self):
            return (exec, ('import os',))

    payload = pickle.dumps(ExecExploit())

    # act
    with pytest.raises(
        pickle.UnpicklingError, match='Unsafe class',
    ):
        _safe_loads(payload)


def test_safe_loads__os_module__raise_error():

    # arrange
    class OsExploit:
        def __reduce__(self):
            return (os.getcwd, ())

    payload = pickle.dumps(OsExploit())

    # act
    with pytest.raises(
        pickle.UnpicklingError, match='Unsafe class',
    ):
        _safe_loads(payload)


def test_safe_loads__invalid_bytes__raise_error():

    # act
    with pytest.raises(pickle.UnpicklingError):
        _safe_loads(b'not-valid-pickle')


def test_safe_loads__none_value__return_none():

    # act
    result = _safe_loads(pickle.dumps(None))

    # assert
    assert result is None


def test_safe_loads__string__return_string():

    # act
    result = _safe_loads(pickle.dumps('hello'))

    # assert
    assert result == 'hello'


def test_safe_loads__int__return_int():

    # act
    result = _safe_loads(pickle.dumps(42))

    # assert
    assert result == 42


def test_safe_loads__bool__return_bool():

    # act
    result = _safe_loads(pickle.dumps(True))

    # assert
    assert result is True


# --- _validate_auth_data ---


def test_validate__valid_token_data__return_dict():

    # arrange
    data = {
        'user_id': 3685,
        'account_id': 1688,
        'user_agent': 'PostmanRuntime/7.40.0',
        'user_ip': None,
        'for_api_key': False,
        'is_superuser': False,
    }

    # act
    result = _validate_auth_data(data)

    # assert
    assert result == data


def test_validate__valid_token_list__return_list():

    # arrange
    data = ['abcdef1234', 'deadbeef42']

    # act
    result = _validate_auth_data(data)

    # assert
    assert result == data


def test_validate__none__return_none():

    # act
    result = _validate_auth_data(None)

    # assert
    assert result is None


def test_validate__dict_no_user_id__return_none():

    # act
    result = _validate_auth_data(
        {'account_id': 1, 'some_field': 'value'},
    )

    # assert
    assert result is None


def test_validate__list_non_strings__return_none():

    # act
    result = _validate_auth_data(
        ['valid_token', 123, None],
    )

    # assert
    assert result is None


@pytest.mark.parametrize('value', [
    42,
    'raw_string',
    {1, 2, 3},
])
def test_validate__unexpected_type__return_none(value):

    # act
    result = _validate_auth_data(value)

    # assert
    assert result is None


def test_validate__empty_dict__return_none():

    # act
    result = _validate_auth_data({})

    # assert
    assert result is None


def test_validate__empty_list__return_list():

    # act
    result = _validate_auth_data([])

    # assert
    assert result == []


# --- RedisAuthClient ---


@pytest.mark.asyncio
async def test_redis_get__valid_key__return_data(
    redis_auth_client,
    unit_mock_redis_client,
    mock_redis_settings,
):

    # arrange
    expected_data = {'user_id': 1, 'account_id': 2}
    prefix = 'auth:'
    mock_redis_settings.return_value.KEY_PREFIX_REDIS = (
        prefix
    )
    unit_mock_redis_client.get.return_value = (
        pickle.dumps(expected_data)
    )

    # act
    result = await redis_auth_client.get('test-key')

    # assert
    assert result == expected_data
    unit_mock_redis_client.get.assert_called_once_with(
        f'{prefix}test-key',
    )


@pytest.mark.asyncio
async def test_redis_get__none_value__return_none(
    redis_auth_client,
    unit_mock_redis_client,
    mock_redis_settings,
):

    # arrange
    prefix = 'auth:'
    mock_redis_settings.return_value.KEY_PREFIX_REDIS = (
        prefix
    )
    unit_mock_redis_client.get.return_value = None

    # act
    result = await redis_auth_client.get('test-key')

    # assert
    assert result is None
    unit_mock_redis_client.get.assert_called_once_with(
        f'{prefix}test-key',
    )


@pytest.mark.asyncio
async def test_redis_get__rce_payload__raise_error(
    redis_auth_client,
    unit_mock_redis_client,
    mock_redis_settings,
):

    # arrange
    malicious_payload = (
        b"\x80\x04\x95\x1e\x00\x00\x00\x00\x00\x00\x00"
        b"\x8c\x05posix\x8c\x06system\x93"
        b"\x8c\x0becho pwned\x85R."
    )
    mock_redis_settings.return_value.KEY_PREFIX_REDIS = (
        'auth:'
    )
    unit_mock_redis_client.get.return_value = malicious_payload

    # act
    with pytest.raises(RedisOperationError):
        await redis_auth_client.get('test-key')


@pytest.mark.asyncio
async def test_redis_get__redis_error__raise_op_error(
    redis_auth_client,
    unit_mock_redis_client,
    mock_redis_settings,
):

    # arrange
    mock_redis_settings.return_value.KEY_PREFIX_REDIS = (
        'auth:'
    )
    unit_mock_redis_client.get.side_effect = (
        redis.RedisError('Redis connection error')
    )

    # act
    with pytest.raises(RedisOperationError):
        await redis_auth_client.get('test-key')


@pytest.mark.asyncio
async def test_redis_get__conn_error__raise_conn_error(
    redis_auth_client,
    unit_mock_redis_client,
    mock_redis_settings,
):

    # arrange
    mock_redis_settings.return_value.KEY_PREFIX_REDIS = (
        'auth:'
    )
    unit_mock_redis_client.get.side_effect = (
        redis.ConnectionError('Connection failed')
    )

    # act
    with pytest.raises(RedisConnectionError):
        await redis_auth_client.get('test-key')


@pytest.mark.asyncio
async def test_redis_get__unpickling_error__raise_op_error(
    redis_auth_client,
    unit_mock_redis_client,
    mock_redis_settings,
):

    # arrange
    mock_redis_settings.return_value.KEY_PREFIX_REDIS = (
        'auth:'
    )
    unit_mock_redis_client.get.return_value = (
        b'invalid-pickle-data'
    )

    # act
    with pytest.raises(RedisOperationError):
        await redis_auth_client.get('test-key')


# --- get_redis_client singleton ---


@pytest.mark.asyncio
async def test_get_redis__default_url__return_client(
    clear_redis_cache,
    mock_redis_settings,
    mock_redis_from_url,
):

    # arrange
    mock_redis_settings.return_value.AUTH_REDIS_URL = (
        'redis://localhost:6379/1'
    )
    mock_redis_from_url.return_value = AsyncMock()

    # act
    result = get_redis_client()

    # assert
    assert isinstance(result, RedisAuthClient)
    mock_redis_from_url.assert_called_once_with(
        'redis://localhost:6379/1',
    )


@pytest.mark.asyncio
async def test_get_redis__twice__same_instance(
    clear_redis_cache,
    mock_redis_settings,
    mock_redis_from_url,
):

    # arrange
    mock_redis_settings.return_value.AUTH_REDIS_URL = (
        'redis://localhost:6379/1'
    )
    mock_redis_from_url.return_value = AsyncMock()

    # act
    first = get_redis_client()
    second = get_redis_client()

    # assert
    assert first is second
    mock_redis_from_url.assert_called_once_with(
        'redis://localhost:6379/1',
    )


@pytest.mark.asyncio
async def test_get_redis__after_clear__new_instance(
    clear_redis_cache,
    mock_redis_settings,
    mock_redis_from_url,
):

    # arrange
    mock_redis_settings.return_value.AUTH_REDIS_URL = (
        'redis://localhost:6379/1'
    )
    mock_redis_from_url.return_value = AsyncMock()
    first = get_redis_client()
    get_redis_client.cache_clear()
    mock_redis_from_url.return_value = AsyncMock()

    # act
    second = get_redis_client()

    # assert
    assert first is not second


# --- close_redis_client ---


@pytest.mark.asyncio
async def test_close_redis__calls_aclose(
    clear_redis_cache,
    mock_redis_settings,
    mock_redis_from_url,
):

    # arrange
    mock_redis_settings.return_value.AUTH_REDIS_URL = (
        'redis://localhost:6379/1'
    )
    mock_underlying = AsyncMock()
    mock_redis_from_url.return_value = mock_underlying
    get_redis_client()

    # act
    await close_redis_client()

    # assert
    mock_underlying.aclose.assert_called_once_with()


@pytest.mark.asyncio
async def test_close_redis__clears_cache(
    clear_redis_cache,
    mock_redis_settings,
    mock_redis_from_url,
):

    # arrange
    mock_redis_settings.return_value.AUTH_REDIS_URL = (
        'redis://localhost:6379/1'
    )
    mock_redis_from_url.return_value = AsyncMock()
    first = get_redis_client()
    await close_redis_client()
    mock_redis_from_url.return_value = AsyncMock()

    # act
    second = get_redis_client()

    # assert
    assert first is not second
