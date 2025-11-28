from unittest.mock import AsyncMock

import pytest
import redis.asyncio as redis
from src.shared_kernel.auth.token_auth import PneumaticToken


class TestPneumaticToken:
    """Test PneumaticToken."""

    @pytest.mark.asyncio
    async def test_data__valid_token__return_data(
        self,
        mock_get_redis_client,
        mocker,
    ):
        """Test successful token data retrieval."""
        # Arrange
        token = 'test-token'
        expected_data = {'user_id': 1, 'account_id': 2}
        encrypted_token = 'encrypted-token-hash'

        encrypt_mock = mocker.patch(
            'src.shared_kernel.auth.token_auth.PneumaticToken.encrypt',
            return_value=encrypted_token,
        )

        mock_redis_client = AsyncMock()
        mock_redis_client.get.return_value = expected_data

        mock_get_redis_client.return_value = mock_redis_client

        # Act
        result = await PneumaticToken.data(token)

        # Assert
        assert result == expected_data
        encrypt_mock.assert_called_once_with(token)
        mock_redis_client.get.assert_called_once_with(encrypted_token)

    @pytest.mark.asyncio
    async def test_data__no_data_found__return_none(
        self,
        mock_get_redis_client,
        mocker,
    ):
        """Test token data retrieval when no data found."""
        # Arrange
        token = 'test-token'
        encrypted_token = 'encrypted-token-hash'

        encrypt_mock = mocker.patch(
            'src.shared_kernel.auth.token_auth.PneumaticToken.encrypt',
            return_value=encrypted_token,
        )

        mock_redis_client = AsyncMock()
        mock_redis_client.get.return_value = None

        mock_get_redis_client.return_value = mock_redis_client

        # Act
        result = await PneumaticToken.data(token)

        # Assert
        assert result is None
        encrypt_mock.assert_called_once_with(token)
        mock_redis_client.get.assert_called_once_with(encrypted_token)

    @pytest.mark.asyncio
    async def test_data__redis_error__raise_exception(
        self,
        mock_get_redis_client,
        mocker,
    ):
        """Test token data retrieval with Redis error."""
        # Arrange
        token = 'test-token'
        encrypted_token = 'encrypted-token-hash'

        encrypt_mock = mocker.patch(
            'src.shared_kernel.auth.token_auth.PneumaticToken.encrypt',
            return_value=encrypted_token,
        )

        mock_redis_client = AsyncMock()
        mock_redis_client.get.side_effect = redis.RedisError('Redis error')

        mock_get_redis_client.return_value = mock_redis_client

        # Act & Assert
        with pytest.raises(redis.RedisError):
            await PneumaticToken.data(token)

        encrypt_mock.assert_called_once_with(token)
        mock_redis_client.get.assert_called_once_with(encrypted_token)
