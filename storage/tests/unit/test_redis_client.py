import pickle
from unittest.mock import AsyncMock

import pytest
import redis.asyncio as redis
from src.shared_kernel.auth.redis_client import (
    RedisAuthClient,
    get_redis_client,
)
from src.shared_kernel.exceptions import (
    RedisConnectionError,
    RedisOperationError,
)


class TestRedisAuthClient:
    """Test RedisAuthClient"""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client"""
        mock_client = AsyncMock()
        return mock_client

    @pytest.fixture
    def redis_auth_client(self, mock_redis_client, mock_redis_from_url):
        """RedisAuthClient instance with mocked Redis"""
        mock_redis_from_url.return_value = mock_redis_client
        client = RedisAuthClient('redis://localhost:6379')
        return client

    @pytest.mark.asyncio
    async def test_get__valid_key__return_data(
        self,
        redis_auth_client,
        mock_redis_client,
        mock_get_settings,
    ):
        """Test successful get operation"""
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
        call_args = mock_redis_client.get.call_args[0]
        assert call_args[0].endswith('test-key')

    @pytest.mark.asyncio
    async def test_get__none_value__return_none(
        self,
        redis_auth_client,
        mock_redis_client,
        mock_get_settings,
    ):
        """Test get operation with None value"""
        # Arrange
        key = 'test-key'

        mock_get_settings.return_value.KEY_PREFIX_REDIS = 'auth:'
        mock_redis_client.get.return_value = None

        # Act
        result = await redis_auth_client.get(key)

        # Assert
        assert result is None
        mock_redis_client.get.assert_called_once()
        call_args = mock_redis_client.get.call_args[0]
        assert call_args[0].endswith('test-key')

    @pytest.mark.asyncio
    async def test_get__redis_error__raise_operation_error(
        self,
        redis_auth_client,
        mock_redis_client,
        mock_get_settings,
    ):
        """Test get operation with Redis error"""
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
        """Test get operation with Redis connection error"""
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
        """Test get operation with unpacking error"""
        # Arrange
        key = 'test-key'
        invalid_data = b'invalid-pickle-data'

        mock_get_settings.return_value.KEY_PREFIX_REDIS = 'auth:'
        mock_redis_client.get.return_value = invalid_data

        # Act & Assert
        with pytest.raises(RedisOperationError):
            await redis_auth_client.get(key)


class TestGetRedisClient:
    """Test get_redis_client function"""

    @pytest.mark.asyncio
    async def test_get_redis_client__default_url__return_client(
        self,
        mock_get_settings,
        mock_redis_from_url,
    ):
        """Test get_redis_client function"""
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
        call_args = mock_redis_from_url.call_args[0]
        assert call_args[0].endswith('/1')
