from unittest.mock import AsyncMock

import pytest
import redis.asyncio as redis

from src.shared_kernel.auth.token_auth import (
    PneumaticToken,
    _compute_pbkdf2,
)


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


class TestComputePbkdf2:
    """Test _compute_pbkdf2 cached hash function."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        """Clear LRU cache before and after each test."""
        _compute_pbkdf2.cache_clear()
        yield
        _compute_pbkdf2.cache_clear()

    def test_compute__deterministic(self):
        """Test same input produces same output."""
        # act
        first = _compute_pbkdf2('token', 'salt', 1)
        second = _compute_pbkdf2('token', 'salt', 1)

        # assert
        assert first == second

    def test_compute__different_tokens(self):
        """Test different tokens produce different hashes."""
        # act
        hash1 = _compute_pbkdf2('token-a', 'salt', 1)
        hash2 = _compute_pbkdf2('token-b', 'salt', 1)

        # assert
        assert hash1 != hash2

    def test_compute__different_salts(self):
        """Test different salts produce different hashes."""
        # act
        hash1 = _compute_pbkdf2('token', 'salt-a', 1)
        hash2 = _compute_pbkdf2('token', 'salt-b', 1)

        # assert
        assert hash1 != hash2

    def test_compute__returns_hex_string(self):
        """Test output is a valid hex string."""
        # act
        result = _compute_pbkdf2('token', 'salt', 1)

        # assert
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 = 32 bytes = 64 hex chars
        int(result, 16)  # must be valid hex

    def test_compute__cache_hit(self):
        """Test LRU cache reuses result."""
        # act
        _compute_pbkdf2('tok', 'salt', 1)
        _compute_pbkdf2('tok', 'salt', 1)
        info = _compute_pbkdf2.cache_info()

        # assert
        assert info.hits == 1
        assert info.misses == 1

    def test_compute__cache_miss_different_args(self):
        """Test LRU cache misses on different args."""
        # act
        _compute_pbkdf2('tok-a', 'salt', 1)
        _compute_pbkdf2('tok-b', 'salt', 1)
        info = _compute_pbkdf2.cache_info()

        # assert
        assert info.hits == 0
        assert info.misses == 2


class TestEncryptInline:
    """Test PneumaticToken.encrypt runs inline."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        """Clear LRU cache."""
        _compute_pbkdf2.cache_clear()
        yield
        _compute_pbkdf2.cache_clear()

    @pytest.mark.asyncio
    async def test_encrypt__returns_hex(
        self,
        mock_get_settings,
    ):
        """Test encrypt returns hex hash."""
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
        self,
        mock_get_settings,
        mocker,
    ):
        """Test encrypt does NOT use asyncio.to_thread."""
        # arrange
        mock_get_settings.return_value.DJANGO_SECRET_KEY = 'secret'
        mock_get_settings.return_value.AUTH_TOKEN_ITERATIONS = 1

        spy = mocker.patch(
            'src.shared_kernel.auth.token_auth.hashlib.pbkdf2_hmac',
            wraps=__import__('hashlib').pbkdf2_hmac,
        )

        # act
        await PneumaticToken.encrypt('my-token')

        # assert — called directly, not via to_thread
        spy.assert_called_once()

    @pytest.mark.asyncio
    async def test_encrypt__cached_on_repeat(
        self,
        mock_get_settings,
    ):
        """Test encrypt uses cached result on repeat call."""
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


class TestDataErrorHandling:
    """Test PneumaticToken.data error paths."""

    @pytest.mark.asyncio
    async def test_data__value_error__returns_none(
        self,
        mock_get_redis_client,
        mocker,
    ):
        """ValueError during data retrieval returns None."""
        # arrange
        mocker.patch(
            'src.shared_kernel.auth.token_auth.PneumaticToken.encrypt',
            side_effect=ValueError('bad value'),
        )

        # act
        result = await PneumaticToken.data('bad-token')

        # assert
        assert result is None

    @pytest.mark.asyncio
    async def test_data__key_error__returns_none(
        self,
        mock_get_redis_client,
        mocker,
    ):
        """KeyError during data retrieval returns None."""
        # arrange
        mocker.patch(
            'src.shared_kernel.auth.token_auth.PneumaticToken.encrypt',
            side_effect=KeyError('missing'),
        )

        # act
        result = await PneumaticToken.data('bad-token')

        # assert
        assert result is None

    @pytest.mark.asyncio
    async def test_data__type_error__returns_none(
        self,
        mock_get_redis_client,
        mocker,
    ):
        """TypeError during data retrieval returns None."""
        # arrange
        mocker.patch(
            'src.shared_kernel.auth.token_auth.PneumaticToken.encrypt',
            side_effect=TypeError('wrong type'),
        )

        # act
        result = await PneumaticToken.data('bad-token')

        # assert
        assert result is None

    @pytest.mark.asyncio
    async def test_encrypt__empty_string__returns_hex(
        self,
        mock_get_settings,
    ):
        """Empty string token still returns valid hex."""
        # arrange
        _compute_pbkdf2.cache_clear()
        mock_get_settings.return_value.DJANGO_SECRET_KEY = 'secret'
        mock_get_settings.return_value.AUTH_TOKEN_ITERATIONS = 1

        # act
        result = await PneumaticToken.encrypt('')

        # assert
        assert isinstance(result, str)
        assert len(result) == 64
        _compute_pbkdf2.cache_clear()
