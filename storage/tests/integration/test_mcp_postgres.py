"""PostgreSQL proves upload concurrency and commit failure safety."""

import asyncio
import importlib
import os
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, call

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from pytest_mock import MockerFixture
from sqlalchemy import event, func, inspect, select, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session

from src.application.dto import UploadFileCommand
from src.application.use_cases.mcp_cleanup import MCPCleanupService
from src.application.use_cases.mcp_upload import MCPUploadService
from src.shared_kernel.config import BaseAppSettings
from src.shared_kernel.database.models import (
    FileRecordORM,
    MCPDownloadTicketORM,
    MCPUploadAttemptORM,
    MCPUploadORM,
)
from src.shared_kernel.middleware.auth_middleware import AuthUser


async def test_concurrent__uploads_commit_one_object__ok(
    postgres_factory: async_sessionmaker[AsyncSession],
    pg_upload: tuple[BaseAppSettings, AuthUser, AsyncMock],
    mcp_command: UploadFileCommand,
):
    # arrange
    settings, user, storage = pg_upload
    first_started, release = asyncio.Event(), asyncio.Event()

    async def store(**kwargs: Any):
        first_started.set()
        await release.wait()

    storage.upload_file.side_effect = store

    async def attempt(command: UploadFileCommand):
        async with postgres_factory() as session:
            return await MCPUploadService(
                session=session, storage=storage, settings=settings
            ).execute(command=command, user=user)

    # act
    first = asyncio.create_task(coro=attempt(command=mcp_command))
    await asyncio.wait_for(fut=first_started.wait(), timeout=5)
    second_command = replace(mcp_command, file_stream=BytesIO(b'abc'))
    second = asyncio.create_task(coro=attempt(command=second_command))
    release.set()
    results = await asyncio.wait_for(
        fut=asyncio.gather(first, second), timeout=10
    )

    # assert
    assert results[0][0].file_id == results[1][0].file_id
    assert results[0][1] is True
    assert results[1][1] is False
    storage.upload_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='object',
        file_stream=mcp_command.file_stream,
        content_type='text/plain',
    )
    storage.delete_file.assert_not_awaited()
    async with postgres_factory() as session:
        assert (
            await session.scalar(
                statement=select(func.count()).select_from(MCPUploadORM)
            )
            == 1
        )
        assert (
            await session.scalar(
                statement=select(func.count()).select_from(FileRecordORM)
            )
            == 1
        )
        assert (
            await session.get(entity=MCPUploadAttemptORM, ident='session-1')
            is None
        )


async def test_commit__failure_cleans_blob_and_mapping__denied(
    postgres_factory: async_sessionmaker[AsyncSession],
    pg_upload: tuple[BaseAppSettings, AuthUser, AsyncMock],
    mcp_command: UploadFileCommand,
):
    # arrange
    settings, user, storage = pg_upload
    failure = RuntimeError('test commit failure')

    async with postgres_factory() as session:
        transaction = session.sync_session
        commits = 0

        def commit_error(sync_session: Session):
            nonlocal commits
            commits += 1
            if commits == 2:
                raise failure

        event.listen(transaction, 'before_commit', commit_error)

        # act
        with pytest.raises(RuntimeError) as error:
            await MCPUploadService(
                session=session, storage=storage, settings=settings
            ).execute(command=mcp_command, user=user)

    # assert
    assert error.value is failure
    storage.upload_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='object',
        file_stream=mcp_command.file_stream,
        content_type='text/plain',
    )
    storage.delete_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='object',
    )
    async with postgres_factory() as session:
        assert (
            await session.scalar(
                statement=select(func.count()).select_from(MCPUploadORM)
            )
            == 0
        )


async def test_failed__writer_cleanup_does_not_delete_successful_retry__ok(
    postgres_factory: async_sessionmaker[AsyncSession],
    pg_upload: tuple[BaseAppSettings, AuthUser, AsyncMock],
    mcp_command: UploadFileCommand,
    delayed_cleanup: tuple[
        type[MCPUploadService], asyncio.Event, asyncio.Event
    ],
):
    # arrange
    settings, user, storage = pg_upload
    delayed, first_cleanup, winner_done = delayed_cleanup
    failed_once = False

    async def store(**kwargs: Any):
        nonlocal failed_once
        if not failed_once:
            failed_once = True
            message = 'failed first upload'
            raise RuntimeError(message)

    storage.upload_file.side_effect = store

    async def loser():
        async with postgres_factory() as session:
            with pytest.raises(RuntimeError):
                await delayed(
                    session=session, storage=storage, settings=settings
                ).execute(command=mcp_command, user=user)

    # act
    first = asyncio.create_task(coro=loser())
    await asyncio.wait_for(fut=first_cleanup.wait(), timeout=5)
    async with postgres_factory() as session:
        await MCPUploadService(
            session=session, storage=storage, settings=settings
        ).execute(command=mcp_command, user=user)
    winner_done.set()
    await asyncio.wait_for(fut=first, timeout=5)

    # assert
    assert storage.upload_file.await_count == 2
    storage.upload_file.assert_has_awaits(
        [
            call(
                bucket_name='bucket',
                file_path='object',
                file_stream=mcp_command.file_stream,
                content_type='text/plain',
            ),
            call(
                bucket_name='bucket',
                file_path='object',
                file_stream=mcp_command.file_stream,
                content_type='text/plain',
            ),
        ],
    )
    storage.delete_file.assert_not_awaited()


@pytest.mark.parametrize('repeat_cancel', [False, True])
async def test_cancelled__blob_write_finishes_cleanup_before_reraising__ok(
    postgres_factory: async_sessionmaker[AsyncSession],
    pg_upload: tuple[BaseAppSettings, AuthUser, AsyncMock],
    repeat_cancel: bool,
    mcp_command: UploadFileCommand,
):
    # arrange
    settings, user, storage = pg_upload
    written, deleting, release = (
        asyncio.Event(),
        asyncio.Event(),
        asyncio.Event(),
    )

    async def store(**kwargs: Any):
        assert kwargs['file_stream'].read() == b'abc'
        written.set()
        await asyncio.Event().wait()

    async def delete_blob(**kwargs: Any):
        deleting.set()
        await release.wait()

    storage.upload_file.side_effect = store
    storage.delete_file.side_effect = delete_blob

    async def upload():
        async with postgres_factory() as session:
            await MCPUploadService(
                session=session, storage=storage, settings=settings
            ).execute(command=mcp_command, user=user)

    # act
    task = asyncio.create_task(coro=upload())
    await asyncio.wait_for(fut=written.wait(), timeout=5)
    task.cancel()
    await asyncio.wait_for(fut=deleting.wait(), timeout=5)
    if repeat_cancel:
        task.cancel()
        await asyncio.sleep(0)

    pending_before_release = not task.done()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(fut=task, timeout=5)

    # assert
    assert pending_before_release
    storage.upload_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='object',
        file_stream=mcp_command.file_stream,
        content_type='text/plain',
    )
    storage.delete_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='object',
    )
    async with postgres_factory() as session:
        assert (
            await session.scalar(
                statement=select(func.count()).select_from(
                    MCPUploadAttemptORM
                ),
            )
            == 0
        )
        assert (
            await session.scalar(
                statement=select(func.count()).select_from(MCPUploadORM),
            )
            == 0
        )
        assert (
            await session.scalar(
                statement=select(func.count()).select_from(FileRecordORM),
            )
            == 0
        )


async def test_hard__process_exit_orphan_recovered_from_durable_journa__ok(
    postgres_factory: async_sessionmaker[AsyncSession],
    pg_upload: tuple[BaseAppSettings, AuthUser, AsyncMock],
    tmp_path: Path,
    mocker: MockerFixture,
):
    # arrange
    _, _, storage = pg_upload
    async with postgres_factory() as session:
        connection = await session.connection()
        schema = connection.sync_connection.get_execution_options()[
            'schema_translate_map'
        ][None]
    helper = Path(__file__).with_name('mcp_crash_upload.py')
    env = {
        **os.environ,
        'PYTHONPATH': str(helper.parents[2]),
        'CONFIG': 'Testing',
        'DJANGO_SECRET_KEY': 'isolated-crash-test-secret',
    }

    # act
    child = await asyncio.create_subprocess_exec(
        sys.executable,
        str(helper),
        schema,
        str(tmp_path),
        env=env,
        cwd=tmp_path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, errors = await asyncio.wait_for(fut=child.communicate(), timeout=15)

    async with postgres_factory() as session:
        attempt = await session.get(
            entity=MCPUploadAttemptORM, ident='session-1'
        )
        file_id = attempt.file_id
        written_bytes = (tmp_path / file_id).read_bytes()
        committed_mapping = await session.get(
            entity=MCPUploadORM, ident='session-1'
        )
        committed_record = await session.get(
            entity=FileRecordORM, ident=file_id
        )
        attempt.created_at = datetime.now(UTC) - timedelta(hours=25)
        await session.commit()
    core = mocker.patch(
        'src.shared_kernel.auth.mcp.MCPCoreClient.post',
        return_value={'eligible': True},
    )
    storage.get_storage_path.return_value = ('test-10', file_id)

    async def delete_blob(**kwargs: Any):
        (tmp_path / kwargs['file_path']).unlink(missing_ok=True)

    storage.delete_file.side_effect = delete_blob
    async with postgres_factory() as session:
        result = await MCPCleanupService(
            session=session, storage=storage
        ).execute()
        recovered_attempt = await session.get(
            entity=MCPUploadAttemptORM, ident='session-1'
        )

    # assert
    assert child.returncode == 73, errors.decode()
    assert written_bytes == b'crash-surviving-bytes'
    assert committed_mapping is None
    assert committed_record is None
    assert result == {'examined': 1, 'deleted': 1, 'skipped': 0}
    assert recovered_attempt is None
    storage.delete_file.assert_awaited_once_with(
        bucket_name='test-10',
        file_path=file_id,
    )
    assert not (tmp_path / file_id).exists()
    core.assert_awaited_once_with(
        path='/internal/mcp/cleanup-upload',
        body={
            'upload_session_id': 'session-1',
            'file_id': file_id,
            'account_id': 10,
            'user_id': 1,
        },
    )


async def test_mcp__migration_roundtrip_preserves_ordinary_files__ok(
    postgres_factory: async_sessionmaker[AsyncSession],
):
    # arrange
    migration = importlib.import_module(
        'src.shared_kernel.database.migrations.versions.'
        '6ba2db086f1b_mcp_file_capabilities'
    )
    mcp_tables = (
        MCPUploadORM.__table__,
        MCPUploadAttemptORM.__table__,
        MCPDownloadTicketORM.__table__,
    )
    expected_columns = {
        table.name: {column.name: column.nullable for column in table.columns}
        for table in mcp_tables
    }
    expected_indexes = {
        table.name: {index.name for index in table.indexes}
        for table in mcp_tables
    }
    expected_primary_keys = {
        table.name: set(table.primary_key.columns.keys())
        for table in mcp_tables
    }

    # act
    async with postgres_factory() as session:
        connection = await session.connection()

        def roundtrip(conn: Connection):
            schema = conn.get_execution_options()['schema_translate_map'][None]
            conn.execute(
                text("SELECT set_config('search_path', :schema, true)"),
                {'schema': schema},
            )
            MCPDownloadTicketORM.__table__.drop(conn)
            MCPUploadORM.__table__.drop(conn)
            MCPUploadAttemptORM.__table__.drop(conn)
            conn.execute(
                FileRecordORM.__table__.insert().values(
                    file_id='ordinary-kept',
                    size=3,
                    account_id=10,
                    user_id=1,
                    created_at=datetime.now(UTC),
                )
            )
            with Operations.context(MigrationContext.configure(conn)):
                migration.upgrade()
                inspector = inspect(conn)
                upgraded_columns = {
                    table.name: {
                        column['name']: column['nullable']
                        for column in inspector.get_columns(
                            table.name,
                            schema=schema,
                        )
                    }
                    for table in mcp_tables
                }
                upgraded_indexes = {
                    table.name: {
                        index['name']
                        for index in inspector.get_indexes(
                            table.name,
                            schema=schema,
                        )
                        if not index.get('duplicates_constraint')
                    }
                    for table in mcp_tables
                }
                upgraded_primary_keys = {
                    table.name: set(
                        inspector.get_pk_constraint(
                            table.name,
                            schema=schema,
                        )['constrained_columns'],
                    )
                    for table in mcp_tables
                }
                upgraded_tables = set(
                    inspector.get_table_names(schema=schema),
                )
                migration.downgrade()
            return {
                'columns': upgraded_columns,
                'indexes': upgraded_indexes,
                'primary_keys': upgraded_primary_keys,
                'tables': upgraded_tables,
                'remaining_tables': set(
                    inspect(conn).get_table_names(schema=schema),
                ),
                'ordinary_file': conn.scalar(
                    statement=select(FileRecordORM.file_id),
                ),
            }

        result = await connection.run_sync(roundtrip)
        await session.commit()

    # assert
    assert result['columns'] == expected_columns
    assert result['indexes'] == expected_indexes
    assert result['primary_keys'] == expected_primary_keys
    assert result['tables'] == {
        'files',
        'mcp_uploads',
        'mcp_upload_attempts',
        'mcp_download_tickets',
    }
    assert result['remaining_tables'] == {'files'}
    assert result['ordinary_file'] == 'ordinary-kept'
