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


class TestRestrictedUnpickler:
    """Test _safe_loads blocks RCE payloads (CWE-502)."""

    def test_safe_loads__valid_dict__return_dict(self):
        """Safe built-in dict passes through."""

        # act
        data = {'user_id': 1, 'account_id': 2}
        result = _safe_loads(pickle.dumps(data))

        # assert
        assert result == data

    def test_safe_loads__valid_list__return_list(self):
        """Safe built-in list passes through."""

        # act
        data = ['token_hex_1', 'token_hex_2']
        result = _safe_loads(pickle.dumps(data))

        # assert
        assert result == data

    def test_safe_loads__valid_nested__return_nested(self):
        """Nested safe types pass through."""

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

    def test_safe_loads__os_system__raise_error(self):
        """RCE via os.system is blocked."""

        # arrange
        payload = (
            b"\x80\x04\x95\x1e\x00\x00\x00\x00\x00\x00\x00"
            b"\x8c\x05posix\x8c\x06system\x93"
            b"\x8c\x0becho pwned\x85R."
        )

        # act & assert
        with pytest.raises(
            pickle.UnpicklingError, match='Unsafe class',
        ):
            _safe_loads(payload)

    def test_safe_loads__subprocess__raise_error(self):
        """RCE via subprocess is blocked."""

        # arrange
        class Exploit:
            def __reduce__(self):
                return (subprocess.call, (['echo', 'pwned'],))

        payload = pickle.dumps(Exploit())

        # act & assert
        with pytest.raises(
            pickle.UnpicklingError, match='Unsafe class',
        ):
            _safe_loads(payload)

    def test_safe_loads__eval__raise_error(self):
        """RCE via builtins.eval is blocked (not in whitelist)."""

        # arrange
        class EvalExploit:
            def __reduce__(self):
                return (eval, ('1+1',))

        payload = pickle.dumps(EvalExploit())

        # act & assert
        with pytest.raises(
            pickle.UnpicklingError, match='Unsafe class',
        ):
            _safe_loads(payload)

    def test_safe_loads__exec__raise_error(self):
        """RCE via builtins.exec is blocked."""

        # arrange
        class ExecExploit:
            def __reduce__(self):
                return (exec, ('import os',))

        payload = pickle.dumps(ExecExploit())

        # act & assert
        with pytest.raises(
            pickle.UnpicklingError, match='Unsafe class',
        ):
            _safe_loads(payload)

    def test_safe_loads__os_module__raise_error(self):
        """Instantiation of os module classes is blocked."""

        # arrange
        class OsExploit:
            def __reduce__(self):
                return (os.getcwd, ())

        payload = pickle.dumps(OsExploit())

        # act & assert
        with pytest.raises(
            pickle.UnpicklingError, match='Unsafe class',
        ):
            _safe_loads(payload)

    def test_safe_loads__invalid_bytes__raise_error(self):
        """Corrupt data raises UnpicklingError."""

        # act & assert
        with pytest.raises(pickle.UnpicklingError):
            _safe_loads(b'not-valid-pickle')

    def test_safe_loads__none_value__return_none(self):
        """Pickled None passes through."""

        # act
        result = _safe_loads(pickle.dumps(None))

        # assert
        assert result is None

    def test_safe_loads__string__return_string(self):
        """Pickled string passes through."""

        # act
        result = _safe_loads(pickle.dumps('hello'))

        # assert
        assert result == 'hello'

    def test_safe_loads__int__return_int(self):
        """Pickled int passes through."""

        # act
        result = _safe_loads(pickle.dumps(42))

        # assert
        assert result == 42

    def test_safe_loads__bool__return_bool(self):
        """Pickled bool passes through."""

        # act
        result = _safe_loads(pickle.dumps(True))

        # assert
        assert result is True


class TestValidateAuthData:
    """Test _validate_auth_data structure validation."""

    def test_validate__valid_token_data__return_dict(self):
        """Valid token data with user_id passes."""

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

    def test_validate__valid_token_list__return_list(self):
        """Valid list of hex token strings passes."""

        # act
        data = ['abcdef1234', 'deadbeef42']
        result = _validate_auth_data(data)

        # assert
        assert result == data

    def test_validate__none__return_none(self):
        """None input returns None."""

        # act & assert
        assert _validate_auth_data(None) is None

    def test_validate__dict_without_user_id__return_none(self):
        """Dict missing user_id is rejected."""

        # act & assert
        assert _validate_auth_data(
            {'account_id': 1, 'some_field': 'value'},
        ) is None

    def test_validate__list_with_non_strings__return_none(self):
        """Token list with non-string items is rejected."""

        # act & assert
        assert _validate_auth_data(
            ['valid_token', 123, None],
        ) is None

    @pytest.mark.parametrize('value', [
        42,
        'raw_string',
        {1, 2, 3},
    ])
    def test_validate__unexpected_type__return_none(
        self,
        value,
    ):
        """Unexpected types are rejected."""

        # act & assert
        assert _validate_auth_data(value) is None

    def test_validate__empty_dict__return_none(self):
        """Empty dict (no user_id) is rejected."""

        # act & assert
        assert _validate_auth_data({}) is None

    def test_validate__empty_list__return_list(self):
        """Empty list is valid (user with no active tokens)."""

        # act & assert
        assert _validate_auth_data([]) == []


class TestRedisAuthClient:
    """Test RedisAuthClient."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        return AsyncMock()

    @pytest.fixture
    def redis_auth_client(self, mock_redis_client, mock_redis_from_url):
        """RedisAuthClient instance with mocked Redis."""
        mock_redis_from_url.return_value = mock_redis_client
        return RedisAuthClient('redis://localhost:6379')

    @pytest.mark.asyncio
    async def test_get__valid_key__return_data(
        self,
        redis_auth_client,
        mock_redis_client,
        mock_get_settings,
    ):
        """Test successful get operation."""
        # Arrange
        key = 'test-key'
        expected_data = {'user_id': 1, 'account_id': 2}
        pickled_data = pickle.dumps(expected_data)

        mock_get_settings.return_value.KEY_PREFIX_REDIS = 'auth:'
        mock_redis_client.get.return_value = pickled_data

        # Act
        result = await redis_auth_client.get(key)

        # Assert
        assert result == expected_data
        mock_redis_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get__none_value__return_none(
        self,
        redis_auth_client,
        mock_redis_client,
        mock_get_settings,
    ):
        """Test get operation with None value."""
        # Arrange
        key = 'test-key'

        mock_get_settings.return_value.KEY_PREFIX_REDIS = 'auth:'
        mock_redis_client.get.return_value = None

        # Act
        result = await redis_auth_client.get(key)

        # Assert
        assert result is None
        mock_redis_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get__rce_payload__raise_operation_error(
        self,
        redis_auth_client,
        mock_redis_client,
        mock_get_settings,
    ):
        """Test that RCE payload from compromised Redis is blocked."""
        # Arrange
        key = 'test-key'
        # Malicious payload: os.system('echo pwned')
        malicious_payload = (
            b"\x80\x04\x95\x1e\x00\x00\x00\x00\x00\x00\x00"
            b"\x8c\x05posix\x8c\x06system\x93"
            b"\x8c\x0becho pwned\x85R."
        )
        mock_get_settings.return_value.KEY_PREFIX_REDIS = 'auth:'
        mock_redis_client.get.return_value = malicious_payload

        # Act & Assert
        with pytest.raises(RedisOperationError):
            await redis_auth_client.get(key)

    @pytest.mark.asyncio
    async def test_get__redis_error__raise_operation_error(
        self,
        redis_auth_client,
        mock_redis_client,
        mock_get_settings,
    ):
        """Test get operation with Redis error."""
        # Arrange
        key = 'test-key'

        mock_get_settings.return_value.KEY_PREFIX_REDIS = 'auth:'
        mock_redis_client.get.side_effect = redis.RedisError(
            'Redis connection error',
        )

        # Act & Assert
        with pytest.raises(RedisOperationError):
            await redis_auth_client.get(key)

    @pytest.mark.asyncio
    async def test_get__connection_error__raise_connection_error(
        self,
        redis_auth_client,
        mock_redis_client,
        mock_get_settings,
    ):
        """Test get operation with Redis connection error."""
        # Arrange
        key = 'test-key'

        mock_get_settings.return_value.KEY_PREFIX_REDIS = 'auth:'
        mock_redis_client.get.side_effect = redis.ConnectionError(
            'Connection failed',
        )

        # Act & Assert
        with pytest.raises(RedisConnectionError):
            await redis_auth_client.get(key)

    @pytest.mark.asyncio
    async def test_get__unpickling_error__raise_operation_error(
        self,
        redis_auth_client,
        mock_redis_client,
        mock_get_settings,
    ):
        """Test get operation with unpacking error."""
        # Arrange
        key = 'test-key'
        invalid_data = b'invalid-pickle-data'

        mock_get_settings.return_value.KEY_PREFIX_REDIS = 'auth:'
        mock_redis_client.get.return_value = invalid_data

        # Act & Assert
        with pytest.raises(RedisOperationError):
            await redis_auth_client.get(key)


class TestGetRedisClient:
    """Test get_redis_client singleton function."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        """Clear lru_cache before and after each test."""
        get_redis_client.cache_clear()
        yield
        get_redis_client.cache_clear()

    @pytest.mark.asyncio
    async def test_get_redis_client__default_url__return_client(
        self,
        mock_get_settings,
        mock_redis_from_url,
    ):
        """Test get_redis_client function."""
        # Arrange
        expected_url = 'redis://localhost:6379/1'

        mock_get_settings.return_value.AUTH_REDIS_URL = expected_url
        mock_client = AsyncMock()
        mock_redis_from_url.return_value = mock_client

        # Act
        result = get_redis_client()

        # Assert
        assert isinstance(result, RedisAuthClient)
        mock_redis_from_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_redis__twice__same_instance(
        self,
        mock_get_settings,
        mock_redis_from_url,
    ):
        """Test get_redis_client returns same instance."""
        # arrange
        mock_get_settings.return_value.AUTH_REDIS_URL = (
            'redis://localhost:6379/1'
        )
        mock_redis_from_url.return_value = AsyncMock()

        # act
        first = get_redis_client()
        second = get_redis_client()

        # assert
        assert first is second
        # from_url called only once due to lru_cache
        mock_redis_from_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_redis__after_clear__new_inst(
        self,
        mock_get_settings,
        mock_redis_from_url,
    ):
        """Test new instance after cache clear."""
        # arrange
        mock_get_settings.return_value.AUTH_REDIS_URL = (
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


class TestCloseRedisClient:
    """Test close_redis_client shutdown function."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        """Clear lru_cache before and after each test."""
        get_redis_client.cache_clear()
        yield
        get_redis_client.cache_clear()

    @pytest.mark.asyncio
    async def test_close__calls_aclose(
        self,
        mock_get_settings,
        mock_redis_from_url,
    ):
        """Test close_redis_client closes connection."""
        # arrange
        mock_get_settings.return_value.AUTH_REDIS_URL = (
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
    async def test_close__clears_cache(
        self,
        mock_get_settings,
        mock_redis_from_url,
    ):
        """Test close clears lru_cache for fresh instance."""
        # arrange
        mock_get_settings.return_value.AUTH_REDIS_URL = (
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
