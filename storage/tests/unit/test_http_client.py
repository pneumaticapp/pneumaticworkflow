from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import Request
from src.infra.http_client import HttpClient
from src.shared_kernel.auth.user_types import UserType
from src.shared_kernel.exceptions import (
    HttpClientError,
    HttpTimeoutError,
)
from src.shared_kernel.middleware.auth_middleware import AuthUser


class TestHttpClient:
    """Test HttpClient"""

    @pytest.fixture
    def http_client(self):
        """HTTP client instance"""
        return HttpClient(base_url='http://test.example.com')

    @pytest.fixture
    def mock_request(self):
        """Mock request"""
        request = Mock(spec=Request)
        request.headers = {}
        request.cookies = {}
        return request

    @pytest.mark.asyncio
    async def test_check_file_permission__valid_token__return_true(
        self,
        http_client,
        mock_request,
        mock_httpx_post,
    ):
        """Test successful file permission check"""
        # Arrange
        file_id = 'test-file-id'
        token = 'valid-token'
        user = AuthUser(
            auth_type=UserType.AUTHENTICATED,
            user_id=1,
            account_id=1,
            token=token,
        )

        mock_response = AsyncMock()
        mock_response.status_code = 204  # NO_CONTENT
        mock_httpx_post.return_value = mock_response

        # Act
        result = await http_client.check_file_permission(user, file_id)

        # Assert
        assert result is True
        mock_httpx_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_file_permission__access_denied__return_false(
        self,
        http_client,
        mock_request,
        mock_httpx_post,
    ):
        """Test file permission check denied"""
        # Arrange
        file_id = 'test-file-id'
        token = 'valid-token'
        user = AuthUser(
            auth_type=UserType.AUTHENTICATED,
            user_id=1,
            account_id=1,
            token=token,
        )

        mock_response = AsyncMock()
        mock_response.status_code = 403  # FORBIDDEN
        mock_httpx_post.return_value = mock_response

        # Act
        result = await http_client.check_file_permission(user, file_id)

        # Assert
        assert result is False
        mock_httpx_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_file_permission__http_error__return_false(
        self,
        http_client,
        mock_request,
        mock_httpx_post,
    ):
        """Test file permission check with HTTP error"""
        # Arrange
        file_id = 'test-file-id'
        token = 'valid-token'
        user = AuthUser(
            auth_type=UserType.AUTHENTICATED,
            user_id=1,
            account_id=1,
            token=token,
        )

        mock_httpx_post.side_effect = httpx.RequestError('HTTP error')

        # Act & Assert
        with pytest.raises(HttpClientError):
            await http_client.check_file_permission(user, file_id)

    @pytest.mark.asyncio
    async def test_check_file_permission__timeout_error__raise_timeout_error(
        self,
        http_client,
        mock_request,
        mock_httpx_post,
    ):
        """Test file permission check with timeout error"""
        # Arrange
        file_id = 'test-file-id'
        token = 'valid-token'
        user = AuthUser(
            auth_type=UserType.AUTHENTICATED,
            user_id=1,
            account_id=1,
            token=token,
        )

        mock_httpx_post.side_effect = httpx.TimeoutException('Timeout')

        # Act & Assert
        with pytest.raises(HttpTimeoutError):
            await http_client.check_file_permission(user, file_id)

    @pytest.mark.asyncio
    async def test_check_file_permission__cookie_token__return_true(
        self,
        http_client,
        mock_request,
        mock_httpx_post,
    ):
        """Test file permission check with cookie token"""
        # Arrange
        file_id = 'test-file-id'
        token = 'session-token'
        user = AuthUser(
            auth_type=UserType.GUEST_TOKEN,
            user_id=None,
            account_id=None,
            token=token,
        )

        mock_response = AsyncMock()
        mock_response.status_code = 204  # NO_CONTENT
        mock_httpx_post.return_value = mock_response

        # Act
        result = await http_client.check_file_permission(user, file_id)

        # Assert
        assert result is True
        mock_httpx_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_file_permission__no_auth__return_false(
        self,
        http_client,
        mock_request,
        mock_httpx_post,
    ):
        """Test file permission check without auth"""
        # Arrange
        file_id = 'test-file-id'
        user = AuthUser(
            auth_type=UserType.ANONYMOUS,
            user_id=None,
            account_id=None,
            token=None,
        )

        mock_response = AsyncMock()
        mock_response.status_code = 401  # UNAUTHORIZED
        mock_httpx_post.return_value = mock_response

        # Act
        result = await http_client.check_file_permission(user, file_id)

        # Assert
        assert result is False
        mock_httpx_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_file_permission__server_error__return_false(
        self,
        http_client,
        mock_request,
        mock_httpx_post,
    ):
        """Test file permission check with 500 response"""
        # Arrange
        file_id = 'test-file-id'
        token = 'valid-token'
        user = AuthUser(
            auth_type=UserType.AUTHENTICATED,
            user_id=1,
            account_id=1,
            token=token,
        )

        mock_response = AsyncMock()
        mock_response.status_code = 500  # INTERNAL_SERVER_ERROR
        mock_httpx_post.return_value = mock_response

        # Act
        result = await http_client.check_file_permission(user, file_id)

        # Assert
        assert result is False
        mock_httpx_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_close__valid_client__close_successfully(self, http_client):
        """Test client close"""
        # Arrange
        mock_client = AsyncMock()
        http_client._client = mock_client

        # Act
        await http_client.close()

        # Assert
        mock_client.aclose.assert_called_once()
        assert http_client._client is None

    @pytest.mark.asyncio
    async def test_close__client_none__do_nothing(self, http_client):
        """Test client close when client is None"""
        # Arrange
        http_client._client = None

        # Act
        await http_client.close()

        # Assert
        assert http_client._client is None
