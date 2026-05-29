from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import Request

from src.infra.http_client import HttpClient, SharedClientHolder
from src.shared_kernel.auth.user_types import UserType
from src.shared_kernel.exceptions import (
    HttpClientError,
    HttpTimeoutError,
)
from src.shared_kernel.middleware.auth_middleware import AuthUser


class TestHttpClient:
    """Test HttpClient."""

    @pytest.fixture
    def http_client(self):
        """HTTP client instance."""
        return HttpClient(base_url='http://test.example.com')

    @pytest.fixture
    def mock_request(self):
        """Mock request."""
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
        """Test successful file permission check."""
        # Arrange
        file_id = '12345678-1234-5678-1234-567812345678'
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
        """Test file permission check denied."""
        # Arrange
        file_id = '12345678-1234-5678-1234-567812345678'
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
        """Test file permission check with HTTP error."""
        # Arrange
        file_id = '12345678-1234-5678-1234-567812345678'
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
        """Test file permission check with timeout error."""
        # Arrange
        file_id = '12345678-1234-5678-1234-567812345678'
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
        """Test file permission check with cookie token."""
        # Arrange
        file_id = '12345678-1234-5678-1234-567812345678'
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
        """Test file permission check without auth."""
        # Arrange
        file_id = '12345678-1234-5678-1234-567812345678'
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
        """Test file permission check with 500 response."""
        # Arrange
        file_id = '12345678-1234-5678-1234-567812345678'
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

        assert result is False
        mock_httpx_post.assert_called_once()


class TestSharedClientHolder:
    """Test SharedClientHolder timeout configuration."""

    @pytest.fixture(autouse=True)
    def _reset_holder(self):
        """Reset holder between tests."""
        SharedClientHolder._instance = None
        yield
        SharedClientHolder._instance = None

    def test_get__creates_client_with_timeout(self):
        """Client is created with explicit timeout."""

        # act
        client = SharedClientHolder.get()

        # assert
        assert client.timeout.read == 30.0
        assert client.timeout.connect == 10.0

    def test_get__singleton__same_instance(self):
        """Multiple calls return same instance."""

        # act
        client1 = SharedClientHolder.get()
        client2 = SharedClientHolder.get()

        # assert
        assert client1 is client2

    def test_timeout_constant__properly_defined(self):
        """Timeout constant is properly defined."""

        # act & assert
        assert isinstance(
            SharedClientHolder._TIMEOUT, httpx.Timeout,
        )
        assert SharedClientHolder._TIMEOUT.read == 30.0
        assert SharedClientHolder._TIMEOUT.connect == 10.0

    @pytest.mark.asyncio
    async def test_close__has_instance__cleanup(self):
        """Close cleans up the client."""
        SharedClientHolder.get()
        assert SharedClientHolder._instance is not None

        # act
        await SharedClientHolder.close()

        # assert
        assert SharedClientHolder._instance is None

    @pytest.mark.asyncio
    async def test_close__no_instance__no_error(self):
        """Close with no instance does nothing."""

        # act & assert — no error
        await SharedClientHolder.close()
