"""Tests for HttpClient and SharedClientHolder."""

from unittest.mock import AsyncMock

import httpx
import pytest

from src.infra.http_client import SharedClientHolder
from src.shared_kernel.auth.user_types import UserType
from src.shared_kernel.exceptions import (
    HttpClientError,
    HttpTimeoutError,
)
from src.shared_kernel.middleware.auth_middleware import AuthUser

# --- HttpClient.check_file_permission ---


@pytest.mark.asyncio
async def test_check_permission__valid_token__true(
    http_client,
    mock_httpx_post,
):

    # arrange
    file_id = '12345678-1234-5678-1234-567812345678'
    user = AuthUser(
        auth_type=UserType.AUTHENTICATED,
        user_id=1,
        account_id=1,
        token='valid-token',
    )
    mock_response = AsyncMock()
    mock_response.status_code = 204
    mock_httpx_post.return_value = mock_response

    # act
    result = await http_client.check_file_permission(
        user=user, file_id=file_id,
    )

    # assert
    assert result is True
    mock_httpx_post.assert_called_once_with(
        url='http://test.example.com',
        data={'file_id': file_id},
        headers={
            'Authorization': 'Bearer valid-token',
        },
    )


@pytest.mark.asyncio
async def test_check_permission__denied__false(
    http_client,
    mock_httpx_post,
):

    # arrange
    file_id = '12345678-1234-5678-1234-567812345678'
    user = AuthUser(
        auth_type=UserType.AUTHENTICATED,
        user_id=1,
        account_id=1,
        token='valid-token',
    )
    mock_response = AsyncMock()
    mock_response.status_code = 403
    mock_httpx_post.return_value = mock_response

    # act
    result = await http_client.check_file_permission(
        user=user, file_id=file_id,
    )

    # assert
    assert result is False
    mock_httpx_post.assert_called_once_with(
        url='http://test.example.com',
        data={'file_id': file_id},
        headers={
            'Authorization': 'Bearer valid-token',
        },
    )


@pytest.mark.asyncio
async def test_check_permission__http_error__raise(
    http_client,
    mock_httpx_post,
):

    # arrange
    file_id = '12345678-1234-5678-1234-567812345678'
    user = AuthUser(
        auth_type=UserType.AUTHENTICATED,
        user_id=1,
        account_id=1,
        token='valid-token',
    )
    mock_httpx_post.side_effect = httpx.RequestError(
        'HTTP error',
    )

    # act
    with pytest.raises(HttpClientError):
        await http_client.check_file_permission(
            user=user, file_id=file_id,
        )


@pytest.mark.asyncio
async def test_check_permission__timeout__raise(
    http_client,
    mock_httpx_post,
):

    # arrange
    file_id = '12345678-1234-5678-1234-567812345678'
    user = AuthUser(
        auth_type=UserType.AUTHENTICATED,
        user_id=1,
        account_id=1,
        token='valid-token',
    )
    mock_httpx_post.side_effect = httpx.TimeoutException(
        'Timeout',
    )

    # act
    with pytest.raises(HttpTimeoutError):
        await http_client.check_file_permission(
            user=user, file_id=file_id,
        )


@pytest.mark.asyncio
async def test_check_permission__cookie_token__true(
    http_client,
    mock_httpx_post,
):

    # arrange
    file_id = '12345678-1234-5678-1234-567812345678'
    user = AuthUser(
        auth_type=UserType.GUEST_TOKEN,
        user_id=None,
        account_id=None,
        token='session-token',
    )
    mock_response = AsyncMock()
    mock_response.status_code = 204
    mock_httpx_post.return_value = mock_response

    # act
    result = await http_client.check_file_permission(
        user=user, file_id=file_id,
    )

    # assert
    assert result is True
    mock_httpx_post.assert_called_once_with(
        url='http://test.example.com',
        data={'file_id': file_id},
        headers={
            'X-Guest-Authorization': 'session-token',
        },
    )


@pytest.mark.asyncio
async def test_check_permission__no_auth__false(
    http_client,
    mock_httpx_post,
):

    # arrange
    file_id = '12345678-1234-5678-1234-567812345678'
    user = AuthUser(
        auth_type=UserType.ANONYMOUS,
        user_id=None,
        account_id=None,
        token=None,
    )
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_httpx_post.return_value = mock_response

    # act
    result = await http_client.check_file_permission(
        user=user, file_id=file_id,
    )

    # assert
    assert result is False
    mock_httpx_post.assert_called_once_with(
        url='http://test.example.com',
        data={'file_id': file_id},
        headers={},
    )


@pytest.mark.asyncio
async def test_check_permission__server_error__false(
    http_client,
    mock_httpx_post,
):

    # arrange
    file_id = '12345678-1234-5678-1234-567812345678'
    user = AuthUser(
        auth_type=UserType.AUTHENTICATED,
        user_id=1,
        account_id=1,
        token='valid-token',
    )
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_httpx_post.return_value = mock_response

    # act
    result = await http_client.check_file_permission(
        user=user, file_id=file_id,
    )

    # assert
    assert result is False
    mock_httpx_post.assert_called_once_with(
        url='http://test.example.com',
        data={'file_id': file_id},
        headers={
            'Authorization': 'Bearer valid-token',
        },
    )


# --- SharedClientHolder ---


def test_get__creates_client_with_timeout(
    reset_shared_client_holder,
):

    # act
    client = SharedClientHolder.get()

    # assert
    assert client.timeout.read == 30.0
    assert client.timeout.connect == 10.0


def test_get__singleton__same_instance(
    reset_shared_client_holder,
):

    # act
    client1 = SharedClientHolder.get()
    client2 = SharedClientHolder.get()

    # assert
    assert client1 is client2


def test_timeout_constant__properly_defined(
    reset_shared_client_holder,
):

    # act
    timeout = SharedClientHolder._TIMEOUT

    # assert
    assert isinstance(timeout, httpx.Timeout)
    assert timeout.read == 30.0
    assert timeout.connect == 10.0


@pytest.mark.asyncio
async def test_close__has_instance__cleanup(
    reset_shared_client_holder,
):

    # arrange
    SharedClientHolder.get()
    assert SharedClientHolder._instance is not None

    # act
    await SharedClientHolder.close()

    # assert
    assert SharedClientHolder._instance is None


@pytest.mark.asyncio
async def test_close__no_instance__no_error(
    reset_shared_client_holder,
):

    # act — no error
    await SharedClientHolder.close()
