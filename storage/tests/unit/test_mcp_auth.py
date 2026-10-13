"""Test the trusted core client and its strict response contract."""

import json
from collections.abc import Callable
from time import time
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import Request
from pytest_mock import MockerFixture

from src.shared_kernel.auth.dependencies import AuthenticatedUser
from src.shared_kernel.auth.mcp import (
    MCPCoreClient,
    authenticate_mcp_request,
)
from src.shared_kernel.config import BaseAppSettings
from src.shared_kernel.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    error_messages as messages,
)
from src.shared_kernel.exceptions.mcp_exceptions import (
    MCPCoreUnavailableError,
    MCPUploadConflictError,
)


async def test_core__service_auth_no_original_token_or_env_proxy__ok(
    core_transport: tuple[Any, ...],
):
    # arrange
    _, _, requests, options = core_transport

    # act
    grant = await MCPCoreClient().validate(
        credential='mcp-d_opaque',
        operation='download',
        file_id='file-1',
    )

    # assert
    assert grant.user_id == 3
    assert (
        requests[0].url == 'http://core.internal/internal/mcp/validate-files'
    )
    assert requests[0].headers['authorization'] == (
        'Bearer storage-only-secret-for-tests-1234'
    )
    assert b'mcp-d_opaque' in requests[0].content
    assert options[0]['trust_env'] is False
    assert options[0]['follow_redirects'] is False
    assert grant.user().mcp_authorization_expires_at == grant.expires_at
    assert (
        AuthenticatedUser(auth_user=grant.user()).mcp_authorization_expires_at
        == grant.expires_at
    )


@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('active', False),
        ('active', 'true'),
        ('user_id', 0),
        ('user_id', True),
        ('account_id', '10'),
        ('connection_id', ''),
        ('operation', 'upload'),
    ],
)
async def test_strict__grant_denies_malformed_or_inactive__ok(
    core_transport: tuple[Any, ...],
    field: str,
    value: Any,
):
    # arrange
    core_transport[1][field] = value
    expected = (
        AuthenticationError
        if field == 'active' and value is False
        else PermissionDeniedError
        if field == 'operation'
        else MCPCoreUnavailableError
    )

    # act
    with pytest.raises(expected) as ex:
        await MCPCoreClient().validate(operation='download', file_id='file-1')

    # assert
    assert ex.value.error_code.message == (
        messages.MSG_AUTH_001
        if expected is AuthenticationError
        else messages.MSG_PERM_001
        if expected is PermissionDeniedError
        else messages.MSG_MCP_001
    )


async def test_connection__mismatch_denied__denied(
    core_transport: tuple[Any, ...],
):
    # arrange

    # act
    with pytest.raises(AuthenticationError) as ex:
        await MCPCoreClient().validate(
            operation='download',
            connection_id='foreign',
            file_id='file-1',
        )

    # assert
    assert ex.value.error_code.message == messages.MSG_AUTH_001


async def test_mcp__disabled_never_contacts_core__ok(
    core_transport: tuple[Any, ...],
):
    # arrange
    core_transport[0].MCP_ENABLED = False

    # act
    with pytest.raises(AuthenticationError) as ex:
        await MCPCoreClient().validate(operation='download')

    # assert
    assert not core_transport[2]

    assert ex.value.error_code.message == messages.MSG_AUTH_001


async def test_core__timeout_fails_closed__ok(mocker: MockerFixture):
    # arrange
    settings = BaseAppSettings(
        MCP_ENABLED=True,
        MCP_FILE_SERVICE_SECRET='test-secret-for-storage-validation-1234',
    )
    settings_mock = mocker.patch(
        'src.shared_kernel.auth.mcp.get_settings', return_value=settings
    )
    client = AsyncMock()
    client.post.side_effect = httpx.ReadTimeout('timeout')
    client.__aenter__.return_value = client
    client_mock = mocker.patch(
        'src.shared_kernel.auth.mcp.httpx.AsyncClient', return_value=client
    )

    # act
    with pytest.raises(MCPCoreUnavailableError) as ex:
        await MCPCoreClient().validate(operation='download')

    # assert
    assert ex.value.error_code.message == messages.MSG_MCP_001

    client_mock.assert_called_once_with(
        trust_env=False,
        timeout=10,
        follow_redirects=False,
    )
    client.post.assert_awaited_once_with(
        settings.MCP_BACKEND_URL + '/internal/mcp/validate-files',
        headers={
            'Authorization': 'Bearer test-secret-for-storage-validation-1234'
        },
        json={'operation': 'download'},
    )
    settings_mock.assert_called_once_with()


@pytest.mark.parametrize(
    ('status', 'error'),
    [
        (401, MCPCoreUnavailableError),
        (403, PermissionDeniedError),
        (500, MCPCoreUnavailableError),
        (302, MCPCoreUnavailableError),
    ],
)
async def test_core__http_failure_is_sanitized__denied(
    core_transport: tuple[Any, ...],
    mocker: MockerFixture,
    status: int,
    error: Any,
):
    # arrange
    client = AsyncMock()
    client.__aenter__.return_value = client
    client.post.return_value = httpx.Response(
        status, text='private core details'
    )
    client_mock = mocker.patch(
        'src.shared_kernel.auth.mcp.httpx.AsyncClient', return_value=client
    )

    # act
    with pytest.raises(error) as caught:
        await MCPCoreClient().validate(operation='download')

    # assert
    assert 'private core details' not in str(caught.value)

    client_mock.assert_called_once_with(
        trust_env=False,
        timeout=10,
        follow_redirects=False,
    )
    client.post.assert_awaited_once_with(
        'http://core.internal/internal/mcp/validate-files',
        headers={'Authorization': 'Bearer storage-only-secret-for-tests-1234'},
        json={'operation': 'download'},
    )


@pytest.mark.parametrize(
    'expires', [None, True, '1700000000', 1700000000.5, {}]
)
async def test_core__read_expiry_must_be_an_integer__ok(
    core_transport: tuple[Any, ...], expires: Any
):
    # arrange
    core_transport[1]['expires_at'] = expires

    # act
    with pytest.raises(MCPCoreUnavailableError) as ex:
        await MCPCoreClient().validate(operation='download')

    # assert
    assert ex.value.error_code.message == messages.MSG_MCP_001


async def test_core__read_expiry_missing_denied__denied(
    core_transport: tuple[Any, ...],
):
    # arrange
    core_transport[1].pop('expires_at')

    # act
    with pytest.raises(MCPCoreUnavailableError) as ex:
        await MCPCoreClient().validate(operation='download')

    # assert
    assert ex.value.error_code.message == messages.MSG_MCP_001


async def test_core__read_expiry_past_denied__denied(
    core_transport: tuple[Any, ...],
):
    # arrange
    core_transport[1]['expires_at'] = int(time()) - 1

    # act
    with pytest.raises(AuthenticationError) as ex:
        await MCPCoreClient().validate(operation='download')

    # assert
    assert ex.value.error_code.message == messages.MSG_AUTH_001


@pytest.mark.parametrize(
    'raw_path',
    [
        '/mcp/files/my report.txt',
        '/mcp/files/%6Dy%20report.txt',
        '/mcp/files/my%20report%2etxt',
        '/mcp/files/мой файл.txt',
    ],
)
async def test_read__wire_path_must_be_canonical_before_core__ok(
    core_transport: tuple[Any, ...], raw_path: str
):
    # arrange
    file_id = 'мой файл.txt' if 'мой' in raw_path else 'my report.txt'
    request = Request(
        {
            'type': 'http',
            'method': 'GET',
            'path': '/mcp/files/' + file_id,
            'raw_path': raw_path.encode(),
            'root_path': '',
            'query_string': b'',
            'headers': [(b'authorization', b'Bearer mcp-d_read')],
        }
    )

    # act
    with pytest.raises(AuthenticationError) as ex:
        await authenticate_mcp_request(request=request)

    # assert
    assert not core_transport[2]

    assert ex.value.error_code.message == messages.MSG_AUTH_001


@pytest.mark.parametrize(
    'content',
    [
        b'invalid-private-json',
        b'[]',
        b'null',
        b'"private-value"',
        b'1',
        b'true',
    ],
)
async def test_post__invalid_json_or_nonobject__unavailable(
    mcp_http_transport: Callable[..., Any],
    content: bytes,
):
    # arrange
    transport = mcp_http_transport(
        response=httpx.Response(status_code=200, content=content),
    )
    body = {'operation': 'download', 'file_id': 'file-1'}

    # act
    with pytest.raises(MCPCoreUnavailableError) as ex:
        await MCPCoreClient().post(
            path='/internal/mcp/validate-files',
            body=body,
        )

    # assert
    assert ex.value.error_code.message == messages.MSG_MCP_001
    assert ex.value.error_code.code == 'MCP_503'
    assert len(transport['requests']) == 1
    assert str(transport['requests'][0].url) == (
        'http://core.internal/internal/mcp/validate-files'
    )
    assert transport['requests'][0].headers['authorization'] == (
        'Bearer storage-only-secret-for-tests-1234'
    )
    assert json.loads(transport['requests'][0].content) == body
    transport['settings_mock'].assert_called_once_with()
    transport['client_mock'].assert_called_once_with(
        trust_env=False,
        timeout=10,
        follow_redirects=False,
    )


async def test_post__private_core_409__sanitized_conflict(
    mcp_http_transport: Callable[..., Any],
):
    # arrange
    transport = mcp_http_transport(
        response=httpx.Response(
            status_code=409,
            content=b'private conflicting session details',
        ),
    )
    body = {'upload_session_id': 'session-1', 'file_id': 'file-1'}

    # act
    with pytest.raises(MCPUploadConflictError) as ex:
        await MCPCoreClient().post(
            path='/internal/mcp/complete-upload',
            body=body,
        )

    # assert
    assert ex.value.error_code.message == messages.MSG_MCP_002
    assert ex.value.error_code.code == 'MCP_409'
    assert len(transport['requests']) == 1
    assert str(transport['requests'][0].url) == (
        'http://core.internal/internal/mcp/complete-upload'
    )
    assert transport['requests'][0].headers['authorization'] == (
        'Bearer storage-only-secret-for-tests-1234'
    )
    assert json.loads(transport['requests'][0].content) == body
    transport['settings_mock'].assert_called_once_with()
    transport['client_mock'].assert_called_once_with(
        trust_env=False,
        timeout=10,
        follow_redirects=False,
    )
