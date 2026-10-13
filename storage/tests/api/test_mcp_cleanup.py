"""Cleanup preserves ordinary files and retries behind live core fences."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import call

import pytest
from pytest_mock import MockerFixture
from sqlalchemy import event, func, select
from sqlalchemy.orm import Session

from src.application.use_cases.mcp_cleanup import MCPCleanupService
from src.shared_kernel.database.models import (
    FileRecordORM,
    MCPDownloadTicketORM,
    MCPUploadAttemptORM,
    MCPUploadORM,
)
from src.shared_kernel.exceptions import error_messages as messages
from src.shared_kernel.exceptions.mcp_exceptions import MCPCoreUnavailableError


@pytest.mark.parametrize('eligible', [False, 'true', 1])
async def test_cleanup_uploads__orphan_without_strict_fence__retained(
    mcp_context: dict[str, Any],
    eligible: Any,
    mcp_cleanup_request: Callable[..., Any],
    create_mcp_orphan: Callable[..., Any],
):
    # arrange
    context = mcp_context
    file_id = await create_mcp_orphan(context=context)
    context['core'].side_effect = None
    context['core'].return_value = {'eligible': eligible}

    # act
    response = mcp_cleanup_request(context=context)

    # assert
    assert response.json() == {'examined': 1, 'deleted': 0, 'skipped': 1}
    context['core'].assert_awaited_once_with(
        path='/internal/mcp/cleanup-upload',
        body={
            'upload_session_id': 'session-1',
            'file_id': file_id,
            'account_id': 10,
            'user_id': 1,
        },
    )
    context['storage'].delete_file.assert_not_awaited()
    assert (
        await context['session'].get(
            entity=MCPUploadAttemptORM,
            ident='session-1',
        )
        is not None
    )


async def test_cleanup_uploads__orphan_storage_failure__journal_retained(
    mcp_context: dict[str, Any],
    mcp_cleanup_request: Callable[..., Any],
    create_mcp_orphan: Callable[..., Any],
):
    # arrange
    context = mcp_context
    await create_mcp_orphan(context=context)
    context['core'].side_effect = None
    context['core'].return_value = {'eligible': True}
    failure = RuntimeError('test deletion failure')
    context['storage'].delete_file.side_effect = failure

    # act
    with pytest.raises(RuntimeError) as ex:
        mcp_cleanup_request(context=context)

    # assert
    assert ex.value is failure
    context['storage'].delete_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='path',
    )
    assert (
        await context['session'].get(
            entity=MCPUploadAttemptORM,
            ident='session-1',
        )
        is not None
    )


async def test_cleanup_uploads__stale_journal_with_winner__file_retained(
    mcp_context: dict[str, Any],
    mcp_cleanup_request: Callable[..., Any],
    create_mcp_orphan: Callable[..., Any],
    age_mcp_upload: Callable[..., Any],
):
    # arrange
    context = mcp_context
    file_id = await age_mcp_upload(context=context)
    await create_mcp_orphan(context=context)
    context['core'].side_effect = None
    context['core'].return_value = {'eligible': False}

    # act
    response = mcp_cleanup_request(context=context)

    # assert
    assert response.json() == {'examined': 2, 'deleted': 0, 'skipped': 2}
    context['storage'].delete_file.assert_not_awaited()
    assert (
        await context['session'].get(
            entity=MCPUploadORM,
            ident='session-1',
        )
        is not None
    )

    # Only the committed upload requires a core verdict; the stale journal
    # is independently fenced by its existing file/mapping provenance.
    context['core'].assert_awaited_once_with(
        path='/internal/mcp/cleanup-upload',
        body={
            'upload_session_id': 'session-1',
            'file_id': file_id,
            'account_id': 10,
            'user_id': 1,
        },
    )


async def test_cleanup_uploads__journal_with_ordinary_file__file_retained(
    mcp_context: dict[str, Any],
    mcp_cleanup_request: Callable[..., Any],
    create_mcp_orphan: Callable[..., Any],
):
    # arrange
    context = mcp_context
    file_id = await create_mcp_orphan(context=context)
    context['session'].add(
        instance=FileRecordORM(
            file_id=file_id,
            size=3,
            account_id=10,
            user_id=1,
            created_at=datetime.now(UTC) - timedelta(hours=25),
        ),
    )
    await context['session'].commit()

    # act
    response = mcp_cleanup_request(context=context)

    # assert
    assert response.json() == {'examined': 1, 'deleted': 0, 'skipped': 1}
    context['core'].assert_not_called()
    context['storage'].delete_file.assert_not_awaited()
    assert (
        await context['session'].get(
            entity=FileRecordORM,
            ident=file_id,
        )
        is not None
    )


async def test_cleanup_uploads__ordinary_service_secret__unauthorized(
    mcp_context: dict[str, Any],
    mcp_cleanup_request: Callable[..., Any],
    age_mcp_upload: Callable[..., Any],
):
    # arrange
    await age_mcp_upload(context=mcp_context)

    # act
    response = mcp_cleanup_request(
        context=mcp_context,
        secret='ordinary-owner-token',
    )

    # assert
    assert response.status_code == 401
    assert response.json()['message'] == messages.MSG_AUTH_001
    mcp_context['core'].assert_not_called()
    mcp_context['storage'].delete_file.assert_not_awaited()


async def test_cleanup_uploads__eligible_mapping__only_mcp_deleted(
    mcp_context: dict[str, Any],
    mcp_cleanup_request: Callable[..., Any],
    age_mcp_upload: Callable[..., Any],
):
    # arrange
    context = mcp_context
    file_id = await age_mcp_upload(context=context)
    now = datetime.now(UTC)
    context['session'].add(
        instance=FileRecordORM(
            file_id='ordinary-old',
            size=1,
            content_type='text/plain',
            filename='old.txt',
            user_id=1,
            account_id=10,
            created_at=now - timedelta(days=2),
        ),
    )
    context['session'].add(
        instance=MCPDownloadTicketORM(
            token_hash='a' * 64,
            connection_id='conn-1',
            authorization_id='auth-1',
            user_id=1,
            account_id=10,
            file_id=file_id,
            expires_at=now + timedelta(minutes=5),
        ),
    )
    await context['session'].commit()
    context['core'].side_effect = None
    context['core'].return_value = {'eligible': True}

    # act
    response = mcp_cleanup_request(context=context)

    # assert
    assert response.status_code == 200
    assert response.json() == {'examined': 1, 'deleted': 1, 'skipped': 0}
    context['core'].assert_awaited_once_with(
        path='/internal/mcp/cleanup-upload',
        body={
            'upload_session_id': 'session-1',
            'file_id': file_id,
            'account_id': 10,
            'user_id': 1,
        },
    )
    context['storage'].delete_file.assert_awaited_once_with(
        bucket_name='bucket',
        file_path='path',
    )
    assert (
        await context['session'].scalar(
            statement=select(func.count()).select_from(MCPUploadORM),
        )
        == 0
    )
    assert (
        await context['session'].scalar(
            statement=select(func.count()).select_from(MCPDownloadTicketORM),
        )
        == 0
    )
    assert (
        await context['session'].get(
            entity=FileRecordORM,
            ident='ordinary-old',
        )
        is not None
    )


@pytest.mark.parametrize('orphan', [False, True])
async def test_cleanup_uploads__completed_retry__no_second_delete(
    mcp_context: dict[str, Any],
    mcp_cleanup_request: Callable[..., Any],
    age_mcp_upload: Callable[..., Any],
    create_mcp_orphan: Callable[..., Any],
    orphan: bool,
):
    # arrange
    context = mcp_context
    seed = create_mcp_orphan if orphan else age_mcp_upload
    await seed(context=context)
    context['core'].side_effect = None
    context['core'].return_value = {'eligible': True}
    mcp_cleanup_request(context=context)
    context['core'].reset_mock()
    context['storage'].delete_file.reset_mock()

    # act
    response = mcp_cleanup_request(context=context)

    # assert
    assert response.json() == {'examined': 0, 'deleted': 0, 'skipped': 0}
    context['core'].assert_not_called()
    context['storage'].delete_file.assert_not_awaited()


@pytest.mark.parametrize('verdict', [False, 'true', 1, None])
@pytest.mark.parametrize('orphan', [False, True])
async def test_cleanup_uploads__negative_verdict_retry__backoff(
    mcp_context: dict[str, Any],
    verdict: Any,
    orphan: bool,
    mcp_cleanup_request: Callable[..., Any],
    age_mcp_upload: Callable[..., Any],
    create_mcp_orphan: Callable[..., Any],
):
    # arrange
    context = mcp_context
    seed = create_mcp_orphan if orphan else age_mcp_upload
    file_id = await seed(context=context)
    context['core'].side_effect = None
    context['core'].return_value = (
        {} if verdict is None else {'eligible': verdict}
    )
    mcp_cleanup_request(context=context)
    context['core'].reset_mock()

    # act
    response = mcp_cleanup_request(context=context)

    # assert
    assert response.json() == {'examined': 0, 'deleted': 0, 'skipped': 0}
    context['core'].assert_not_called()
    context['storage'].delete_file.assert_not_awaited()
    if orphan:
        assert (
            await context['session'].get(
                entity=MCPUploadAttemptORM,
                ident='session-1',
            )
            is not None
        )
    else:
        assert (
            await context['session'].get(
                entity=FileRecordORM,
                ident=file_id,
            )
            is not None
        )


async def test_cleanup_uploads__recent_file__no_core_call(
    mcp_context: dict[str, Any],
    mcp_cleanup_request: Callable[..., Any],
    age_mcp_upload: Callable[..., Any],
):
    # arrange
    context = mcp_context
    file_id = await age_mcp_upload(context=context)
    record = await context['session'].get(
        entity=FileRecordORM,
        ident=file_id,
    )
    record.created_at = datetime.now(UTC)
    await context['session'].commit()

    # act
    response = mcp_cleanup_request(context=context)

    # assert
    assert response.json() == {'examined': 0, 'deleted': 0, 'skipped': 0}
    context['core'].assert_not_called()
    context['storage'].delete_file.assert_not_awaited()


async def test_cleanup_uploads__core_outage__file_retained(
    mcp_context: dict[str, Any],
    mcp_cleanup_request: Callable[..., Any],
    age_mcp_upload: Callable[..., Any],
):
    # arrange
    context = mcp_context
    file_id = await age_mcp_upload(context=context)
    context['core'].side_effect = MCPCoreUnavailableError()

    # act
    response = mcp_cleanup_request(context=context)

    # assert
    assert response.status_code == 503
    assert response.json() == {
        'code': 'MCP_503',
        'message': messages.MSG_MCP_001,
    }
    context['core'].assert_awaited_once_with(
        path='/internal/mcp/cleanup-upload',
        body={
            'upload_session_id': 'session-1',
            'file_id': file_id,
            'account_id': 10,
            'user_id': 1,
        },
    )
    context['storage'].delete_file.assert_not_awaited()


@pytest.mark.parametrize('orphan', [False, True])
async def test_cleanup_uploads__storage_failure_retry__journal_recovers(
    mcp_context: dict[str, Any],
    mcp_cleanup_request: Callable[..., Any],
    age_mcp_upload: Callable[..., Any],
    create_mcp_orphan: Callable[..., Any],
    orphan: bool,
):
    # arrange
    context = mcp_context
    seed = create_mcp_orphan if orphan else age_mcp_upload
    await seed(context=context)
    context['core'].side_effect = None
    context['core'].return_value = {'eligible': True}
    context['storage'].delete_file.side_effect = RuntimeError('test deletion')
    with pytest.raises(RuntimeError):
        mcp_cleanup_request(context=context)
    context['storage'].delete_file.side_effect = None

    # act
    response = mcp_cleanup_request(context=context)

    # assert
    assert response.json() == {'examined': 1, 'deleted': 1, 'skipped': 0}
    assert context['storage'].delete_file.await_count == 2
    context['storage'].delete_file.assert_has_awaits(
        [
            call(bucket_name='bucket', file_path='path'),
            call(bucket_name='bucket', file_path='path'),
        ],
    )
    assert (
        await context['session'].get(
            entity=MCPUploadAttemptORM,
            ident='session-1',
        )
        is None
    )
    assert (
        await context['session'].get(
            entity=MCPUploadORM,
            ident='session-1',
        )
        is None
    )


async def test_cleanup_uploads__commit_failure_retry__db_and_blob_deleted(
    mcp_context: dict[str, Any],
    mcp_cleanup_request: Callable[..., Any],
    age_mcp_upload: Callable[..., Any],
):
    # arrange
    context = mcp_context
    file_id = await age_mcp_upload(context=context)
    context['core'].side_effect = None
    context['core'].return_value = {'eligible': True}
    failure = RuntimeError('test database commit failure')
    commits = 0

    def commit_error(session: Session):
        nonlocal commits
        commits += 1
        if commits == 2:
            raise failure

    event.listen(
        target=context['session'].sync_session,
        identifier='before_commit',
        fn=commit_error,
    )
    try:
        with pytest.raises(RuntimeError):
            mcp_cleanup_request(context=context)
    finally:
        event.remove(
            target=context['session'].sync_session,
            identifier='before_commit',
            fn=commit_error,
        )

    # act
    response = mcp_cleanup_request(context=context)

    # assert
    assert response.json() == {'examined': 1, 'deleted': 1, 'skipped': 0}
    assert context['storage'].delete_file.await_count == 2
    context['storage'].delete_file.assert_has_awaits(
        [
            call(bucket_name='bucket', file_path='path'),
            call(bucket_name='bucket', file_path='path'),
        ],
    )
    assert (
        await context['session'].get(
            entity=MCPUploadORM,
            ident='session-1',
        )
        is None
    )
    assert (
        await context['session'].get(
            entity=FileRecordORM,
            ident=file_id,
        )
        is None
    )


@pytest.mark.parametrize(
    ('limit', 'examined'),
    [(None, 100), (-1, 1), (0, 1), (1, 1), (2, 2), (100, 100), (101, 100)],
)
async def test_execute__candidate_limit__bounds_combined_queue(
    mcp_context: dict[str, Any],
    mcp_cleanup_candidates: Callable[..., Any],
    limit: int | None,
    examined: int,
):
    # arrange
    context = mcp_context
    calls = await mcp_cleanup_candidates(
        context=context,
        orphan_count=51,
        upload_count=52,
    )
    expected_calls = calls[:examined]
    context['core'].side_effect = None
    context['core'].return_value = {'eligible': False}
    service = MCPCleanupService(
        session=context['session'],
        storage=context['storage'],
    )

    # act
    result = (
        await service.execute()
        if limit is None
        else (await service.execute(limit=limit))
    )

    # assert
    assert result == {'examined': examined, 'deleted': 0, 'skipped': examined}
    assert context['core'].await_count == examined
    context['core'].assert_has_awaits(expected_calls)
    context['storage'].delete_file.assert_not_awaited()
    assert (
        await context['session'].scalar(
            statement=select(func.count()).select_from(MCPUploadAttemptORM),
        )
        == 51
    )
    assert (
        await context['session'].scalar(
            statement=select(func.count()).select_from(MCPUploadORM),
        )
        == 52
    )
    assert await context['session'].scalar(
        statement=select(func.count())
        .select_from(MCPUploadAttemptORM)
        .where(
            MCPUploadAttemptORM.cleanup_checked_at.is_not(None),
        ),
    ) == min(examined, 51)
    assert await context['session'].scalar(
        statement=select(func.count())
        .select_from(MCPUploadORM)
        .where(
            MCPUploadORM.cleanup_checked_at.is_not(None),
        ),
    ) == max(0, examined - 51)


async def test_execute__overall_deadline__rollback_without_delete(
    mcp_context: dict[str, Any],
    age_mcp_upload: Callable[..., Any],
    mocker: MockerFixture,
):
    # arrange
    context = mcp_context
    file_id = await age_mcp_upload(context=context)
    entered = asyncio.Event()
    real_timeout = asyncio.timeout
    deadline = real_timeout(delay=None)

    async def stalled(path: str, body: dict[str, Any]) -> dict[str, Any]:
        entered.set()
        deadline.reschedule(when=asyncio.get_running_loop().time())
        await asyncio.Event().wait()
        return {'eligible': True}

    context['core'].side_effect = stalled
    timeout_mock = mocker.Mock(return_value=deadline)
    # Replace only this module's dependency binding. The real asyncio module
    # and process clock remain untouched. Expire its real Timeout only after
    # entering the core await, so database scheduling cannot make this flaky.
    mocker.patch(
        'src.application.use_cases.mcp_cleanup.asyncio',
        new=SimpleNamespace(timeout=timeout_mock),
    )
    service = MCPCleanupService(
        session=context['session'],
        storage=context['storage'],
    )

    # act
    with pytest.raises(MCPCoreUnavailableError) as ex:
        await service.execute()

    # assert
    assert ex.value.error_code.message == messages.MSG_MCP_001
    assert ex.value.error_code.code == 'MCP_503'
    assert entered.is_set()
    assert asyncio.timeout is real_timeout
    timeout_mock.assert_called_once_with(60)
    context['core'].assert_awaited_once_with(
        path='/internal/mcp/cleanup-upload',
        body={
            'upload_session_id': 'session-1',
            'file_id': file_id,
            'account_id': 10,
            'user_id': 1,
        },
    )
    context['storage'].delete_file.assert_not_awaited()
    record = await context['session'].get(
        entity=FileRecordORM,
        ident=file_id,
    )
    mapping = await context['session'].get(
        entity=MCPUploadORM,
        ident='session-1',
    )
    assert record.file_id == file_id
    assert mapping.file_id == file_id
    assert mapping.cleanup_checked_at is None
