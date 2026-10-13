"""MCP capabilities are checked for every concrete file request."""

import hashlib
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from io import BytesIO
from typing import Any
from unittest.mock import ANY, call
from urllib.parse import quote
from uuid import NAMESPACE_URL, uuid5

import pytest
from pytest_mock import MockerFixture
from sqlalchemy import func, select

from src.application.dto import DownloadFileQuery, UploadFileCommand
from src.application.use_cases.mcp_upload import MCPUploadService
from src.infra.mappers import FileRecordMapper
from src.infra.url_importer import ImportedFile, UnsafeImportError
from src.shared_kernel.auth.mcp import FileGrant
from src.shared_kernel.database.models import (
    FileRecordORM,
    MCPDownloadTicketORM,
    MCPUploadORM,
)
from src.shared_kernel.exceptions import (
    PermissionDeniedError,
    error_messages as messages,
)
from src.shared_kernel.exceptions.mcp_exceptions import MCPCoreUnavailableError


@pytest.mark.parametrize('credential', ['mcp-d_bad-scope', 'mcp-d_revoked'])
def test_invalid__delegation_never_falls_back_to_owner_cookie__ok(
    mcp_context: dict[str, Any],
    credential: str,
):
    # arrange
    context = mcp_context
    context['client'].cookies.set(name='token', value='ordinary-owner-token')

    # act
    response = context['client'].get(
        url='/file-123',
        headers={'Authorization': f'Bearer {credential}'},
    )

    # assert
    assert response.status_code == 401
    context['ordinary'].assert_not_called()
    context['download'].get_metadata.assert_not_awaited()


def test_wrong__operation_response_denied__denied(
    mcp_context: dict[str, Any], mcp_read_headers: dict[str, str]
):
    # arrange
    mcp_context['core'].side_effect = None
    mcp_context['core'].return_value = {
        **mcp_context['state'],
        'operation': 'upload',
    }

    # act
    response = mcp_context['client'].get(
        url='/file-123', headers=mcp_read_headers
    )

    # assert
    assert response.status_code == 403


@pytest.mark.parametrize(
    'authorization', ['Token mcp-d_revoked', 'mcp-d_revoked']
)
def test_malformed__mcp_scheme_never_falls_back__ok(
    mcp_context: dict[str, Any], authorization: str | bytes
):
    # arrange
    context = mcp_context
    context['client'].cookies.set(name='token', value='ordinary-owner-token')

    # act
    response = context['client'].get(
        url='/file-123', headers={'Authorization': authorization}
    )

    # assert
    assert response.status_code == 401
    context['ordinary'].assert_not_called()


def test_mcp__cookie_never_enters_ordinary_auth__ok(
    mcp_context: dict[str, Any],
):
    # arrange
    context = mcp_context
    context['client'].cookies.set(name='token', value='mcp-d_revoked')

    # act
    response = context['client'].get(url='/file-123')

    # assert
    assert response.status_code == 401
    context['ordinary'].assert_not_called()


def test_foreign__account_owner_denied__denied(
    mcp_context: dict[str, Any], mcp_read_headers: dict[str, str]
):
    # arrange
    mcp_context['state']['account_id'] = 20

    # act
    response = mcp_context['client'].get(
        url='/file-123', headers=mcp_read_headers
    )

    # assert
    assert response.status_code == 404
    mcp_context['download'].get_stream.assert_not_awaited()
    mcp_context['events'].file_access_denied.assert_awaited_once_with(
        user=ANY,
        file_record=mcp_context['record'],
    )


@pytest.mark.parametrize(
    ('range_header', 'active', 'status', 'content'),
    [
        (None, True, 200, b'abcdefgh'),
        ('bytes=2-3', True, 206, b'cd'),
        ('bytes=2-3', False, 401, None),
    ],
)
def test_download_file__each_request__revalidates(
    mcp_context: dict[str, Any],
    mcp_read_headers: dict[str, str],
    range_header: str | None,
    active: bool,
    status: int,
    content: bytes | None,
):
    # arrange
    mcp_context['state']['active'] = active
    headers = dict(mcp_read_headers)
    if range_header is not None:
        headers['Range'] = range_header

    # act
    response = mcp_context['client'].get(url='/file-123', headers=headers)

    # assert
    assert response.status_code == status
    mcp_context['core'].assert_awaited_once_with(
        path='/internal/mcp/validate-files',
        body={
            'credential': 'mcp-d_read',
            'operation': 'download',
            'file_id': 'file-123',
        },
    )
    mcp_context['permission'].check_file_permission.assert_not_awaited()
    if content is not None:
        assert response.content == content
    else:
        assert response.json()['message'] == messages.MSG_AUTH_001
        mcp_context['download'].get_stream.assert_not_awaited()


def test_metadata__rejects_ordinary_token__ok(mcp_context: dict[str, Any]):
    # arrange

    # act
    response = mcp_context['client'].get(
        url='/mcp/files/file-123',
        headers={'Authorization': 'Bearer ordinary'},
    )

    # assert
    assert response.status_code == 401
    mcp_context['ordinary'].assert_not_called()


def test_metadata__sanitizes_legacy_content_type__ok(
    mcp_context: dict[str, Any], mcp_read_headers: dict[str, str]
):
    # arrange
    mcp_context['download'].get_metadata.return_value = replace(
        mcp_context['record'], content_type='text/html; charset=utf-8'
    )

    # act
    response = mcp_context['client'].get(
        url='/mcp/files/file-123', headers=mcp_read_headers
    )

    # assert
    assert response.status_code == 200
    assert response.json()['content_type'] == 'application/octet-stream'
    download = mcp_context['client'].get(
        url='/file-123', headers=mcp_read_headers
    )
    assert download.status_code == 200
    assert download.headers['content-type'] == 'application/octet-stream'


async def test_create_ticket__capability__stores_only_hash(
    mcp_context: dict[str, Any],
    mcp_read_headers: dict[str, str],
):
    # arrange
    session = mcp_context['session']
    session.add(
        instance=FileRecordMapper.entity_to_orm(
            entity=mcp_context['record'],
        )
    )
    await session.commit()

    # act
    response = mcp_context['client'].post(
        url='/mcp/files/file-123/download-ticket',
        headers=mcp_read_headers,
    )
    token = response.json()['download_url'].rsplit('/', 1)[1]
    mapping = await session.get(
        entity=MCPDownloadTicketORM,
        ident=hashlib.sha256(token.encode()).hexdigest(),
    )

    # assert
    assert response.status_code == 200
    assert mapping is not None
    assert mapping.token_hash != token
    assert response.json()['expires_in'] == 300
    assert (mapping.file_id, mapping.connection_id) == ('file-123', 'conn-1')
    assert mapping.authorization_id == 'authorization-1'
    mcp_context['core'].assert_awaited_once_with(
        path='/internal/mcp/validate-files',
        body={
            'credential': 'mcp-d_read',
            'operation': 'download',
            'file_id': 'file-123',
        },
    )


@pytest.mark.parametrize('prefix', ['', '/files'])
@pytest.mark.parametrize('operation', ['metadata', 'download', 'ticket'])
@pytest.mark.parametrize(
    'file_id', ['NiihssB_Drawing (v2).odg', 'мой файл (v2).odg']
)
async def test_root__path_reads_accept_direct_internal_and_public_pref__ok(
    root_mcp_context: dict[str, Any],
    prefix: str,
    operation: str,
    file_id: str,
    mcp_read_headers: dict[str, str],
):
    # arrange
    context = root_mcp_context
    record = replace(context['record'], file_id=file_id)
    context['download'].get_metadata.return_value = record
    context['session'].add(
        instance=FileRecordMapper.entity_to_orm(entity=record)
    )
    await context['session'].commit()
    encoded = quote(file_id, safe='')
    route = ('/' if operation == 'download' else '/mcp/files/') + encoded

    # act
    if operation == 'ticket':
        response = context['client'].post(
            url=prefix + route + '/download-ticket', headers=mcp_read_headers
        )
    else:
        response = context['client'].get(
            url=prefix + route, headers=mcp_read_headers
        )

    # assert
    assert response.status_code == 200
    context['core'].assert_awaited_once_with(
        path='/internal/mcp/validate-files',
        body={
            'credential': 'mcp-d_read',
            'operation': 'metadata' if operation == 'metadata' else 'download',
            'file_id': file_id,
        },
    )


@pytest.mark.parametrize(
    'file_id',
    [
        'NiihssB_Drawing (v2).odg',
        'мой файл (v2).odg',
        'report..v2.pdf',
        'download-ticket',
    ],
)
@pytest.mark.parametrize('operation', ['metadata', 'download', 'ticket'])
async def test_legacy__read_preserves_raw_id_and_encoded_wire_path__ok(
    mcp_context: dict[str, Any],
    file_id: str,
    operation: str,
    mcp_read_headers: dict[str, str],
):
    # arrange
    context = mcp_context
    record = replace(context['record'], file_id=file_id)
    context['download'].get_metadata.return_value = record
    context['session'].add(
        instance=FileRecordMapper.entity_to_orm(entity=record)
    )
    await context['session'].commit()
    encoded = quote(file_id, safe='')

    # act
    if operation == 'download':
        path = '/' + encoded
        response = context['client'].get(url=path, headers=mcp_read_headers)
    elif operation == 'ticket':
        path = '/mcp/files/' + encoded + '/download-ticket'
        response = context['client'].post(url=path, headers=mcp_read_headers)
    else:
        path = '/mcp/files/' + encoded
        response = context['client'].get(url=path, headers=mcp_read_headers)

    # assert
    assert response.status_code == 200
    context['core'].assert_awaited_once_with(
        path='/internal/mcp/validate-files',
        body={
            'credential': 'mcp-d_read',
            'operation': 'metadata' if operation == 'metadata' else 'download',
            'file_id': file_id,
        },
    )
    if operation == 'download':
        context['download'].get_metadata.assert_awaited_once_with(
            DownloadFileQuery(file_id=file_id, user_id=1),
        )
    else:
        context['download'].get_metadata.assert_awaited_once_with(
            query=DownloadFileQuery(file_id=file_id, user_id=1),
        )
    if operation == 'metadata':
        assert response.json()['file_id'] == file_id
    elif operation == 'ticket':
        token = response.json()['download_url'].rsplit('/', 1)[1]
        mapping = await context['session'].get(
            entity=MCPDownloadTicketORM,
            ident=hashlib.sha256(token.encode()).hexdigest(),
        )
        assert mapping.file_id == file_id


@pytest.mark.parametrize(
    'file_id',
    [
        'file/child',
        'file\\child',
        'file?child',
        'file#child',
        'file%2fchild',
        'file\x00child',
        'file\x7fchild',
        '..',
        ' ',
        'file\u200bchild',
        'file\u2028child',
        'file\u2029child',
    ],
)
@pytest.mark.parametrize('prefix', ['', '/mcp/files'])
def test_unsafe__encoded_file_id_denied_before_core__denied(
    mcp_context: dict[str, Any],
    file_id: str,
    prefix: str,
    mcp_read_headers: dict[str, str],
):
    # arrange
    context = mcp_context
    context['client'].cookies.set(name='token', value='ordinary-owner-token')

    # HTTPX normalizes literal dot segments before sending a request.
    encoded = '%2E%2E' if file_id == '..' else quote(file_id, safe='')

    # act
    response = context['client'].get(
        url=prefix + '/' + encoded, headers=mcp_read_headers
    )

    # assert
    assert response.status_code == 401
    context['core'].assert_not_called()
    context['ordinary'].assert_not_called()
    context['download'].get_metadata.assert_not_awaited()


def test_download_ticket__invalid_path__redacted(
    mcp_context: dict[str, Any],
    caplog: Any,
):
    # arrange
    token = 'secret-ticket-' + 'a' * 29

    # act
    response = mcp_context['client'].get(
        url='/mcp/download/' + token + 'x',
    )
    logged = str(caplog.record_tuples)

    # assert
    assert response.status_code == 422
    assert response.json()['code'] == 'VAL_002'
    assert response.json()['message'] == messages.MSG_VAL_007
    assert token not in response.text
    assert '[redacted]' in response.text
    assert token not in logged
    mcp_context['core'].assert_not_called()


def test_ticket__requires_source_authorization_binding__ok(
    mcp_context: dict[str, Any], mcp_read_headers: dict[str, str]
):
    # arrange
    mcp_context['state'].pop('authorization_id')

    # act
    response = mcp_context['client'].post(
        url='/mcp/files/file-123/download-ticket', headers=mcp_read_headers
    )

    # assert
    assert response.status_code == 503
    mcp_context['download'].get_stream.assert_not_awaited()


async def test_ticket__lifetime_clamped_to_source_expiry__ok(
    mcp_context: dict[str, Any], mcp_read_headers: dict[str, str]
):
    # arrange
    context = mcp_context
    core_expiry = int(datetime.now(UTC).timestamp()) + 30
    context['state']['expires_at'] = core_expiry
    context['session'].add(
        instance=FileRecordMapper.entity_to_orm(entity=context['record'])
    )
    await context['session'].commit()

    # act
    response = context['client'].post(
        url='/mcp/files/file-123/download-ticket', headers=mcp_read_headers
    )

    # assert
    assert response.status_code == 200
    result = response.json()
    assert 0 < result['expires_in'] <= 30
    assert (
        datetime.fromisoformat(result['expires_at']).timestamp() == core_expiry
    )
    token = result['download_url'].rsplit('/', 1)[1]
    mapping = await context['session'].get(
        entity=MCPDownloadTicketORM,
        ident=hashlib.sha256(token.encode()).hexdigest(),
    )
    assert mapping.expires_at.replace(tzinfo=UTC).timestamp() == core_expiry


async def test_ticket__subsecond_source_expiry_has_positive_ttl__ok(
    mcp_context: dict[str, Any],
    mocker: MockerFixture,
    mcp_read_headers: dict[str, str],
):
    # arrange
    context = mcp_context
    core_expiry = int(datetime.now(UTC).timestamp()) + 30
    context['state']['expires_at'] = core_expiry
    clock = mocker.patch(
        'src.application.use_cases.mcp_download.datetime', wraps=datetime
    )
    clock.now.return_value = datetime.fromtimestamp(core_expiry - 0.25, UTC)
    context['session'].add(
        instance=FileRecordMapper.entity_to_orm(entity=context['record'])
    )
    await context['session'].commit()

    # act
    response = context['client'].post(
        url='/mcp/files/file-123/download-ticket', headers=mcp_read_headers
    )

    # assert
    assert response.status_code == 200
    result = response.json()
    assert result['expires_in'] == 1
    assert (
        datetime.fromisoformat(result['expires_at']).timestamp() == core_expiry
    )
    token = result['download_url'].rsplit('/', 1)[1]
    mapping = await context['session'].get(
        entity=MCPDownloadTicketORM,
        ident=hashlib.sha256(token.encode()).hexdigest(),
    )
    assert mapping.expires_at.replace(tzinfo=UTC).timestamp() == core_expiry
    clock.now.assert_called_once_with(UTC)
    clock.fromtimestamp.assert_called_once_with(core_expiry, UTC)
    clock.assert_not_called()


@pytest.mark.parametrize(
    'expiry_case', ['missing', 'past', 'string', 'bool', 'float', 'null']
)
async def test_invalid__ticket_expiry_never_persists__ok(
    mcp_context: dict[str, Any],
    expiry_case: str,
    mcp_read_headers: dict[str, str],
):
    # arrange
    context = mcp_context
    if expiry_case == 'missing':
        context['state'].pop('expires_at')
    else:
        context['state']['expires_at'] = {
            'past': int(datetime.now(UTC).timestamp()) - 1,
            'string': str(int(datetime.now(UTC).timestamp()) + 30),
            'bool': True,
            'float': datetime.now(UTC).timestamp() + 30,
            'null': None,
        }[expiry_case]
    context['client'].cookies.set(name='token', value='ordinary-owner-token')

    # act
    response = context['client'].post(
        url='/mcp/files/file-123/download-ticket', headers=mcp_read_headers
    )

    # assert
    assert response.status_code == (401 if expiry_case == 'past' else 503)
    assert (
        await context['session'].scalar(
            statement=select(func.count()).select_from(MCPDownloadTicketORM)
        )
        == 0
    )
    context['ordinary'].assert_not_called()


async def test_upload_file__same_content_retry__one_object_and_audit(
    mcp_context: dict[str, Any],
    mcp_upload_request: Any,
):
    # arrange
    first = mcp_upload_request(context=mcp_context)

    # act
    response = mcp_upload_request(context=mcp_context)
    mappings = await mcp_context['session'].scalar(
        statement=select(func.count()).select_from(MCPUploadORM),
    )
    records = await mcp_context['session'].scalar(
        statement=select(func.count()).select_from(FileRecordORM),
    )

    # assert
    assert response.status_code == 200
    assert response.json() == first.json()
    assert mappings == records == 1
    assert len(mcp_context['callbacks']) == 2
    mcp_context['storage'].upload_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='path',
        file_stream=ANY,
        content_type='text/plain',
    )
    mcp_context['events'].file_upload.assert_awaited_once_with(
        user=ANY,
        file_id=response.json()['file_id'],
        file=ANY,
    )


def test_forged__upload_session_denied__denied(
    mcp_context: dict[str, Any], mcp_upload_request: Callable[..., Any]
):
    # arrange

    # act
    response = mcp_upload_request(context=mcp_context, session='forged-uuid')

    # assert
    assert response.status_code == 401
    mcp_context['storage'].upload_file.assert_not_awaited()
    assert not mcp_context['callbacks']


@pytest.mark.parametrize('operation', ['import', 'cleanup'])
@pytest.mark.parametrize(
    'authorization', [b'Bearer \xff', 'Bearer секрет'.encode()]
)
def test_internal__unicode_authorization_rejected_without_si__denied(
    mcp_context: dict[str, Any],
    mocker: MockerFixture,
    operation: str,
    authorization: str | bytes,
):
    # arrange
    context = mcp_context
    importer = mocker.patch(
        'src.application.use_cases.mcp_import.URLImporter.download'
    )
    body = (
        {
            'credential': 'mcp-u_upload',
            'upload_session_id': 'session-1',
            'url': 'https://example.com/file',
        }
        if operation == 'import'
        else {}
    )

    # act
    response = context['client'].post(
        url='/internal/mcp/' + operation,
        headers=[(b'authorization', authorization)],
        json=body,
    )

    # assert
    assert response.status_code == 401
    context['core'].assert_not_called()
    context['ordinary'].assert_not_called()
    importer.assert_not_awaited()
    context['storage'].upload_file.assert_not_awaited()
    context['storage'].delete_file.assert_not_awaited()


def test_import__requires_internal_service_secret__ok(
    mcp_context: dict[str, Any],
    mocker: MockerFixture,
    mcp_import_request: Callable[..., Any],
):
    # arrange
    importer = mocker.patch(
        'src.application.use_cases.mcp_import.URLImporter.download'
    )

    # act
    response = mcp_import_request(context=mcp_context, secret='ordinary')

    # assert
    assert response.status_code == 401
    importer.assert_not_called()


async def test_import__retry_reconciles_without_redownloading__ok(
    mcp_context: dict[str, Any],
    mocker: MockerFixture,
    mcp_import_request: Callable[..., Any],
):
    # arrange
    importer = mocker.patch(
        'src.application.use_cases.mcp_import.URLImporter.download',
        return_value=ImportedFile(
            stream=BytesIO(b'abc'), size=3, content_type='text/plain'
        ),
    )

    # act
    first, second = (
        mcp_import_request(context=mcp_context),
        mcp_import_request(context=mcp_context),
    )

    # assert
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    importer.assert_awaited_once_with(
        raw_url='https://example.com/file?signature=secret',
    )
    mcp_context['storage'].upload_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='path',
        file_stream=ANY,
        content_type='text/plain',
    )
    mcp_context['events'].file_upload.assert_awaited_once_with(
        user=ANY,
        file_id=str(uuid5(NAMESPACE_URL, 'pneumatic:mcp:session-1')),
        file=ANY,
    )


async def test_upload__mapping_rejects_changed_actor__ok(
    mcp_context: dict[str, Any],
):
    # arrange
    context = mcp_context
    service = MCPUploadService(
        session=context['session'],
        storage=context['storage'],
        settings=context['settings'],
    )
    grant = FileGrant(
        **context['state'],
        operation='upload',
        upload_session_id='session-1',
    )
    command = UploadFileCommand(
        file_stream=BytesIO(b'abc'),
        filename='a.txt',
        content_type='text/plain',
        size=3,
        user_id=1,
        account_id=10,
    )

    await service.execute(
        command=command, user=grant.user(credential='mcp-u_upload')
    )
    grant.account_id = 20

    # act
    with pytest.raises(PermissionDeniedError) as error:
        await service.execute(
            command=command, user=grant.user(credential='mcp-u_upload')
        )

    # assert
    assert error.value.error_code.message == messages.MSG_PERM_001


def test_unavailable__validator_fail_closed__ok(
    mcp_context: dict[str, Any], mcp_read_headers: dict[str, str]
):
    # arrange
    mcp_context['core'].side_effect = MCPCoreUnavailableError()

    # act
    response = mcp_context['client'].get(
        url='/file-123', headers=mcp_read_headers
    )

    # assert
    assert response.status_code == 503
    mcp_context['download'].get_stream.assert_not_awaited()


@pytest.mark.parametrize(
    ('change', 'value'),
    [
        ('active', False),
        ('authorization_id', 'foreign'),
        ('connection_id', 'foreign'),
        ('user_id', 2),
        ('account_id', 20),
        ('expires_at', 1),
    ],
)
async def test_download_ticket__source_revoked__denied(
    mcp_context: dict[str, Any],
    mcp_ticket: str,
    change: str,
    value: Any,
):
    # arrange
    mcp_context['state'][change] = value

    # act
    response = mcp_context['client'].get(
        url='/mcp/download/' + mcp_ticket,
        headers={'Range': 'bytes=2-3'},
    )

    # assert
    assert response.status_code == 401
    assert response.json()['message'] == messages.MSG_AUTH_001
    mcp_context['core'].assert_awaited_once_with(
        path='/internal/mcp/validate-files',
        body={
            'operation': 'download',
            'connection_id': 'conn-1',
            'authorization_id': 'authorization-1',
            'file_id': 'file-123',
        },
    )
    mcp_context['download'].get_stream.assert_not_awaited()
    mcp_context['events'].file_download.assert_not_awaited()


@pytest.mark.parametrize('range_header', [None, 'bytes=2-3'])
async def test_download_ticket__valid_request__private_response(
    mcp_context: dict[str, Any],
    mcp_ticket: str,
    range_header: str | None,
):
    # arrange
    headers = {} if range_header is None else {'Range': range_header}

    # act
    response = mcp_context['client'].get(
        url='/mcp/download/' + mcp_ticket,
        headers=headers,
    )

    # assert
    assert response.status_code == (200 if range_header is None else 206)
    assert response.content == (b'abcdefgh' if range_header is None else b'cd')
    assert response.headers['referrer-policy'] == 'no-referrer'
    assert response.headers['cache-control'] == 'no-store'
    mcp_context['core'].assert_awaited_once_with(
        path='/internal/mcp/validate-files',
        body={
            'operation': 'download',
            'connection_id': 'conn-1',
            'authorization_id': 'authorization-1',
            'file_id': 'file-123',
        },
    )
    mcp_context['download'].get_stream.assert_awaited_once_with(
        file_record=mcp_context['record'],
        range_header=range_header,
    )


async def test_download_ticket__local_expiry__denied_before_core(
    mcp_context: dict[str, Any],
    mcp_ticket: str,
):
    # arrange
    mapping = await mcp_context['session'].get(
        entity=MCPDownloadTicketORM,
        ident=hashlib.sha256(mcp_ticket.encode()).hexdigest(),
    )
    mapping.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await mcp_context['session'].commit()

    # act
    response = mcp_context['client'].get(url='/mcp/download/' + mcp_ticket)

    # assert
    assert response.status_code == 401
    assert response.json()['message'] == messages.MSG_AUTH_001
    mcp_context['core'].assert_not_called()
    mcp_context['download'].get_stream.assert_not_awaited()


async def test_upload_file__different_content_retry__conflict(
    mcp_context: dict[str, Any],
    mcp_upload_request: Any,
):
    # arrange
    mcp_upload_request(context=mcp_context)
    mcp_context['storage'].reset_mock()
    mcp_context['events'].reset_mock()
    mcp_context['core'].reset_mock()

    # act
    response = mcp_upload_request(context=mcp_context, content=b'different')

    # assert
    assert response.status_code == 409
    assert response.json() == {
        'code': 'MCP_409',
        'message': messages.MSG_MCP_002,
    }
    mcp_context['storage'].upload_file.assert_not_awaited()
    mcp_context['events'].file_upload.assert_not_awaited()
    mcp_context['core'].assert_awaited_once_with(
        path='/internal/mcp/validate-files',
        body={
            'credential': 'mcp-u_upload',
            'operation': 'upload',
            'upload_session_id': 'session-1',
        },
    )


@pytest.mark.parametrize('operation', ['upload', 'import'])
async def test_complete__lost_reply_retry__keeps_one_object_and_audit(
    mcp_context: dict[str, Any],
    mocker: MockerFixture,
    operation: str,
    mcp_upload_request: Callable[..., Any],
    mcp_import_request: Callable[..., Any],
):
    # arrange
    context = mcp_context
    stream = BytesIO(b'abc')
    importer_mock = mocker.patch(
        'src.application.use_cases.mcp_import.URLImporter.download',
        return_value=ImportedFile(
            stream=stream,
            size=3,
            content_type='text/plain',
        ),
    )
    original_post = context['core'].side_effect
    lost_once = False

    async def lost_reply(path: str, body: dict[str, Any]) -> dict[str, Any]:
        nonlocal lost_once
        if path == '/internal/mcp/complete-upload' and not lost_once:
            lost_once = True
            raise MCPCoreUnavailableError
        return await original_post(path=path, body=body)

    context['core'].side_effect = lost_reply
    request = (
        mcp_upload_request if operation == 'upload' else mcp_import_request
    )
    request(context=context)
    context['core'].reset_mock()
    file_id = str(uuid5(NAMESPACE_URL, 'pneumatic:mcp:session-1'))
    credential = 'mcp-u_upload' if operation == 'upload' else 'mcp-u_import'
    validation = call(
        path='/internal/mcp/validate-files',
        body={
            'credential': credential,
            'operation': operation,
            'upload_session_id': 'session-1',
        },
    )
    callback_body = {
        'credential': credential,
        'upload_session_id': 'session-1',
        'file_id': file_id,
        'name': 'a.txt',
        'size': 3,
        'content_type': 'text/plain',
    }

    # act
    response = request(context=context)

    # assert
    assert response.status_code == 200
    assert response.json()['file_id'] == file_id
    assert context['callbacks'] == [callback_body]
    assert context['core'].await_count == 3
    context['core'].assert_has_awaits(
        [
            validation,
            validation,
            call(
                path='/internal/mcp/complete-upload',
                body=callback_body,
            ),
        ],
    )
    context['storage'].upload_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='path',
        file_stream=ANY if operation == 'upload' else stream,
        content_type='text/plain',
    )
    context['storage'].delete_file.assert_not_awaited()
    context['events'].file_upload.assert_awaited_once_with(
        user=ANY,
        file_id=file_id,
        file=ANY,
    )
    if operation == 'import':
        importer_mock.assert_awaited_once_with(
            raw_url='https://example.com/file?signature=secret',
        )
        assert stream.closed
    else:
        importer_mock.assert_not_awaited()
    assert (
        await context['session'].scalar(
            statement=select(func.count()).select_from(MCPUploadORM),
        )
        == 1
    )
    assert (
        await context['session'].scalar(
            statement=select(func.count()).select_from(FileRecordORM),
        )
        == 1
    )


async def test_import_file__unsafe_source__standard_error_without_storage(
    mcp_context: dict[str, Any],
    mocker: MockerFixture,
    mcp_import_request: Callable[..., Any],
):
    # arrange
    importer_mock = mocker.patch(
        'src.application.use_cases.mcp_import.URLImporter.download',
        side_effect=UnsafeImportError('private signed source details'),
    )

    # act
    response = mcp_import_request(context=mcp_context)

    # assert
    assert response.status_code == 400
    assert response.json() == {
        'code': 'MCP_400',
        'message': messages.MSG_MCP_003,
    }
    importer_mock.assert_awaited_once_with(
        raw_url='https://example.com/file?signature=secret',
    )
    mcp_context['core'].assert_awaited_once_with(
        path='/internal/mcp/validate-files',
        body={
            'credential': 'mcp-u_import',
            'operation': 'import',
            'upload_session_id': 'session-1',
        },
    )
    mcp_context['storage'].upload_file.assert_not_awaited()
    mcp_context['storage'].delete_file.assert_not_awaited()
    mcp_context['events'].file_upload.assert_not_awaited()
    assert (
        await mcp_context['session'].scalar(
            statement=select(func.count()).select_from(MCPUploadORM),
        )
        == 0
    )
