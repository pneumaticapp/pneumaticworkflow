"""Revocation, durable writes and ownership fences over real ORM state."""

import asyncio
import threading
from collections.abc import Callable
from dataclasses import replace
from io import BytesIO
from typing import Any
from unittest.mock import ANY
from uuid import NAMESPACE_URL, uuid5

import pytest
from pytest_mock import MockerFixture
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.unitofwork import UOWTransaction

from src.application.dto import UploadFileCommand
from src.application.use_cases.mcp_upload import MCPUploadService
from src.infra.url_importer import ImportedFile
from src.shared_kernel.database.models import (
    FileRecordORM,
    MCPUploadAttemptORM,
    MCPUploadORM,
)
from src.shared_kernel.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    error_messages as messages,
)
from src.shared_kernel.exceptions.mcp_exceptions import (
    MCPCoreUnavailableError,
    MCPUploadConflictError,
)
from src.shared_kernel.middleware.auth_middleware import AuthUser


async def test_upload_file__binary_metadata__preserved(
    mcp_context: dict[str, Any],
    mcp_upload_request: Any,
):
    # arrange
    content = b'\x00\xff\x80binary\r\n'
    captured = []

    async def store(**kwargs: Any):
        captured.append(kwargs['file_stream'].read())

    mcp_context['storage'].upload_file.side_effect = store

    # act
    response = mcp_upload_request(context=mcp_context, content=content)
    record = await mcp_context['session'].get(
        entity=FileRecordORM,
        ident=response.json()['file_id'],
    )

    # assert
    assert response.status_code == 200
    assert captured == [content]
    assert (record.user_id, record.account_id) == (1, 10)
    assert (record.filename, record.size, record.content_type) == (
        'a.txt',
        len(content),
        'text/plain',
    )
    assert mcp_context['callbacks'] == [
        {
            'credential': 'mcp-u_upload',
            'upload_session_id': 'session-1',
            'file_id': record.file_id,
            'name': 'a.txt',
            'size': len(content),
            'content_type': 'text/plain',
        }
    ]
    mcp_context['storage'].upload_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='path',
        file_stream=ANY,
        content_type='text/plain',
    )
    mcp_context['storage'].delete_file.assert_not_awaited()


@pytest.mark.parametrize(
    ('change', 'value'),
    [
        ('active', False),
        ('user_id', 2),
        ('account_id', 20),
        ('connection_id', 'different'),
    ],
)
def test_import_file__grant_changed_after_fetch__denied(
    mcp_context: dict[str, Any],
    mocker: MockerFixture,
    change: str,
    value: Any,
    mcp_import_request: Any,
):
    # arrange
    stream = BytesIO(b'abc')

    async def fetched(raw_url: str) -> ImportedFile:
        mcp_context['state'][change] = value
        return ImportedFile(stream=stream, size=3, content_type='text/plain')

    download_mock = mocker.patch(
        'src.application.use_cases.mcp_import.URLImporter.download',
        side_effect=fetched,
    )

    # act
    response = mcp_import_request(context=mcp_context)

    # assert
    assert response.status_code == 401
    assert response.json()['message'] == messages.MSG_AUTH_001
    download_mock.assert_awaited_once_with(
        raw_url='https://example.com/file?signature=secret',
    )
    mcp_context['storage'].upload_file.assert_not_awaited()
    mcp_context['events'].file_upload.assert_not_awaited()
    assert mcp_context['callbacks'] == []
    assert stream.closed


def test_import_file__capability_expired_after_fetch__denied(
    mcp_context: dict[str, Any],
    mocker: MockerFixture,
    mcp_import_request: Any,
):
    # arrange
    stream = BytesIO(b'abc')

    async def fetched(raw_url: str) -> ImportedFile:
        mcp_context['core'].side_effect = AuthenticationError(
            details='Expired',
        )
        return ImportedFile(stream=stream, size=3, content_type='text/plain')

    download_mock = mocker.patch(
        'src.application.use_cases.mcp_import.URLImporter.download',
        side_effect=fetched,
    )

    # act
    response = mcp_import_request(context=mcp_context)

    # assert
    assert response.status_code == 401
    assert response.json()['message'] == messages.MSG_AUTH_001
    download_mock.assert_awaited_once_with(
        raw_url='https://example.com/file?signature=secret',
    )
    mcp_context['storage'].upload_file.assert_not_awaited()
    assert stream.closed


async def test_execute__real_flush_failure__removes_uncommitted_blob(
    mcp_context: dict[str, Any],
    mcp_command: UploadFileCommand,
    mcp_service: MCPUploadService,
    mcp_user: AuthUser,
):
    # arrange
    command = mcp_command

    def collide_insert(
        session: Session,
        flush_context: UOWTransaction,
        instances: Any,
    ):
        pending = next(
            (row for row in session.new if isinstance(row, FileRecordORM)),
            None,
        )
        if pending is not None:
            session.connection().execute(
                FileRecordORM.__table__.insert().values(
                    file_id=pending.file_id,
                    size=1,
                    account_id=10,
                    user_id=1,
                ),
            )

    event.listen(
        target=mcp_context['session'].sync_session,
        identifier='before_flush',
        fn=collide_insert,
    )

    # act
    with pytest.raises(IntegrityError) as ex:
        await mcp_service.execute(command=command, user=mcp_user)
    mappings = await mcp_context['session'].scalar(
        statement=select(func.count()).select_from(MCPUploadORM),
    )
    records = await mcp_context['session'].scalar(
        statement=select(func.count()).select_from(FileRecordORM),
    )

    # assert
    assert ex.value.orig is not None
    assert mappings == 0
    assert records == 0
    mcp_context['storage'].upload_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='path',
        file_stream=command.file_stream,
        content_type='text/plain',
    )
    mcp_context['storage'].delete_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='path',
    )


async def test_execute__partial_object_failure__cleans_up(
    mcp_context: dict[str, Any],
    mcp_command: UploadFileCommand,
    mcp_service: MCPUploadService,
    mcp_user: AuthUser,
):
    # arrange
    failure = RuntimeError('partial object failure')
    mcp_context['storage'].upload_file.side_effect = failure

    # act
    with pytest.raises(RuntimeError) as ex:
        await mcp_service.execute(command=mcp_command, user=mcp_user)

    # assert
    assert ex.value is failure
    mcp_context['storage'].upload_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='path',
        file_stream=mcp_command.file_stream,
        content_type='text/plain',
    )
    mcp_context['storage'].delete_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='path',
    )


async def test_execute__cleanup_failed__keeps_error_and_journal(
    mcp_context: dict[str, Any],
    mcp_command: UploadFileCommand,
    mcp_service: MCPUploadService,
    mcp_user: AuthUser,
):
    # arrange
    failure = RuntimeError('original store failure')
    mcp_context['storage'].upload_file.side_effect = failure
    mcp_context['storage'].delete_file.side_effect = RuntimeError(
        'cleanup failed',
    )

    # act
    with pytest.raises(RuntimeError) as ex:
        await mcp_service.execute(command=mcp_command, user=mcp_user)
    attempt = await mcp_context['session'].get(
        entity=MCPUploadAttemptORM,
        ident='session-1',
    )

    # assert
    assert ex.value is failure
    assert attempt is not None
    assert (attempt.user_id, attempt.account_id) == (1, 10)
    mcp_context['storage'].upload_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='path',
        file_stream=mcp_command.file_stream,
        content_type='text/plain',
    )
    mcp_context['storage'].delete_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='path',
    )


@pytest.mark.parametrize('field', ['account_id', 'user_id'])
async def test_execute__command_owner_mismatch__denied_before_write(
    mcp_context: dict[str, Any],
    mcp_command: UploadFileCommand,
    mcp_service: MCPUploadService,
    mcp_user: AuthUser,
    field: str,
):
    # arrange
    command = replace(mcp_command, **{field: 99})

    # act
    with pytest.raises(PermissionDeniedError) as ex:
        await mcp_service.execute(command=command, user=mcp_user)
    attempt = await mcp_context['session'].get(
        entity=MCPUploadAttemptORM,
        ident='session-1',
    )

    # assert
    assert ex.value.error_code.message == messages.MSG_PERM_001
    assert attempt is None
    mcp_context['core'].assert_not_called()
    mcp_context['storage'].upload_file.assert_not_awaited()
    mcp_context['storage'].delete_file.assert_not_awaited()


async def test_execute__ordinary_record_collision__preserves_record(
    mcp_context: dict[str, Any],
    mcp_command: UploadFileCommand,
    mcp_service: MCPUploadService,
    mcp_user: AuthUser,
):
    # arrange
    file_id = str(uuid5(NAMESPACE_URL, 'pneumatic:mcp:session-1'))
    record = FileRecordORM(
        file_id=file_id,
        size=1,
        account_id=20,
        user_id=2,
    )
    mcp_context['session'].add(instance=record)
    await mcp_context['session'].commit()

    # act
    with pytest.raises(MCPUploadConflictError) as ex:
        await mcp_service.execute(command=mcp_command, user=mcp_user)

    # assert
    assert ex.value.error_code.message == messages.MSG_MCP_002
    kept = await mcp_context['session'].get(
        entity=FileRecordORM,
        ident=file_id,
    )
    assert (kept.user_id, kept.account_id, kept.size) == (2, 20, 1)
    mcp_context['storage'].upload_file.assert_not_awaited()
    mcp_context['storage'].delete_file.assert_not_awaited()


@pytest.mark.parametrize('field', ['account_id', 'user_id'])
async def test_find_completed__record_owner_mismatch__denied(
    mcp_context: dict[str, Any],
    mcp_service: MCPUploadService,
    mcp_user: AuthUser,
    age_mcp_upload: Any,
    field: str,
):
    # arrange
    file_id = await age_mcp_upload(context=mcp_context)
    record = await mcp_context['session'].get(
        entity=FileRecordORM,
        ident=file_id,
    )
    setattr(record, field, 99)
    await mcp_context['session'].commit()

    # act
    with pytest.raises(PermissionDeniedError) as ex:
        await mcp_service.find_completed(user=mcp_user)

    # assert
    assert ex.value.error_code.message == messages.MSG_PERM_001
    mcp_context['core'].assert_not_called()
    mcp_context['storage'].upload_file.assert_not_awaited()


async def test_execute__hash_cancelled_twice__waits_for_reader(
    mcp_context: dict[str, Any],
    mcp_command: UploadFileCommand,
    mcp_service: MCPUploadService,
    mcp_user: AuthUser,
    mocker: MockerFixture,
):
    # arrange
    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()

    def fingerprint(command: UploadFileCommand) -> str:
        started.set()
        release.wait(timeout=5)
        command.file_stream.read()
        finished.set()
        return 'digest'

    fingerprint_mock = mocker.patch(
        'src.application.use_cases.mcp_upload._fingerprint',
        side_effect=fingerprint,
    )
    task = asyncio.create_task(
        coro=mcp_service.execute(command=mcp_command, user=mcp_user),
    )
    await asyncio.to_thread(started.wait, timeout=5)

    task.cancel()
    await asyncio.sleep(0)
    task.cancel()
    await asyncio.sleep(0)
    pending = not task.done()
    release.set()

    # act
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(fut=task, timeout=5)

    # assert
    assert pending
    assert finished.is_set()
    assert not mcp_command.file_stream.closed
    fingerprint_mock.assert_called_once_with(command=mcp_command)
    mcp_context['core'].assert_not_called()
    mcp_context['storage'].upload_file.assert_not_awaited()


def test_upload_file__configured_cap__rejects_before_store(
    mcp_context: dict[str, Any],
    mcp_upload_request: Any,
):
    # arrange
    mcp_context['settings'].MCP_MAX_IMPORT_BYTES = 2

    # act
    response = mcp_upload_request(context=mcp_context, content=b'abc')

    # assert
    assert response.status_code == 413
    assert response.json()['code'] == 'FILE_003'
    mcp_context['storage'].upload_file.assert_not_awaited()
    mcp_context['events'].file_upload.assert_not_awaited()


async def test_find_completed__missing_file__unavailable_without_write(
    mcp_context: dict[str, Any],
    mcp_service: MCPUploadService,
    mcp_user: AuthUser,
    age_mcp_upload: Callable[..., Any],
):
    # arrange
    file_id = await age_mcp_upload(context=mcp_context)
    record = await mcp_context['session'].get(
        entity=FileRecordORM,
        ident=file_id,
    )
    await mcp_context['session'].delete(instance=record)
    await mcp_context['session'].commit()

    # act
    with pytest.raises(MCPCoreUnavailableError) as ex:
        await mcp_service.find_completed(user=mcp_user)

    # assert
    assert ex.value.error_code.message == messages.MSG_MCP_001
    assert ex.value.error_code.code == 'MCP_503'
    assert (
        await mcp_context['session'].get(
            entity=MCPUploadORM,
            ident='session-1',
        )
        is not None
    )
    mcp_context['core'].assert_not_called()
    mcp_context['storage'].upload_file.assert_not_awaited()
    mcp_context['storage'].delete_file.assert_not_awaited()
    mcp_context['events'].file_upload.assert_not_awaited()
