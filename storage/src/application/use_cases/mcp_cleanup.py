"""Delete only aged MCP uploads after core atomically fences attachment."""

# Project convention omits return annotations on procedures.
# mypy: disable-error-code="no-untyped-def"

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, nulls_first, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.mcp_upload import lock_upload_session
from src.infra.adapters.storage_service import StorageService
from src.shared_kernel.auth.mcp import MCPCoreClient
from src.shared_kernel.database.models import (
    FileRecordORM,
    MCPDownloadTicketORM,
    MCPUploadAttemptORM,
    MCPUploadORM,
)
from src.shared_kernel.exceptions.mcp_exceptions import MCPCoreUnavailableError

CLEANUP_MIN_AGE = timedelta(hours=24)
CLEANUP_RECHECK_INTERVAL = timedelta(hours=1)


class MCPCleanupService:
    """A bounded pass over MCP mappings and crash recovery journal entries."""

    def __init__(  # noqa: ANN204
        self,
        session: AsyncSession,
        storage: StorageService,
    ):
        """Bind infrastructure dependencies."""
        self.session = session
        self.storage = storage

    async def _cleanup_one(
        self,
        session_id: str,
        cutoff: datetime,
        now: datetime,
    ) -> int:
        async with self.session.begin():
            await lock_upload_session(
                session=self.session,
                session_id=session_id,
            )
            mapping = await self.session.scalar(
                select(MCPUploadORM)
                .where(
                    MCPUploadORM.session_id == session_id,
                )
                .with_for_update()
            )
            if mapping is None:
                return 0
            record = await self.session.get(FileRecordORM, mapping.file_id)
            created_at = record.created_at if record is not None else None
            if created_at is not None and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=UTC)
            if record is None or (
                record.account_id != mapping.account_id
                or record.user_id != mapping.user_id
                or created_at is None
                or created_at > cutoff
            ):
                return 0
            verdict = await MCPCoreClient().post(
                path='/internal/mcp/cleanup-upload',
                body={
                    'upload_session_id': session_id,
                    'file_id': mapping.file_id,
                    'account_id': mapping.account_id,
                    'user_id': mapping.user_id,
                },
            )
            if verdict.get('eligible') is not True:
                mapping.cleanup_checked_at = now
                return 0
            # Core must lock and mark the session terminal before authorizing.
            # Once fenced, future attach/import/callback operations are denied.
            bucket, path = self.storage.get_storage_path(
                account_id=record.account_id, file_id=record.file_id
            )
            await self.storage.delete_file(bucket_name=bucket, file_path=path)
            await self.session.execute(
                delete(MCPDownloadTicketORM).where(
                    MCPDownloadTicketORM.file_id == record.file_id,
                )
            )
            await self.session.delete(mapping)
            await self.session.delete(record)
        return 1

    async def _cleanup_attempt(  # noqa: PLR0911
        self, session_id: str, cutoff: datetime, now: datetime
    ) -> int:
        async with self.session.begin():
            await lock_upload_session(
                session=self.session,
                session_id=session_id,
            )
            attempt = await self.session.scalar(
                select(MCPUploadAttemptORM)
                .where(MCPUploadAttemptORM.session_id == session_id)
                .with_for_update()
            )
            if attempt is None:
                return 0
            # A successful retry wins. Its file must never be deleted through
            # the orphan path, even if a stale journal row survived.
            if await self.session.get(MCPUploadORM, session_id):
                await self.session.delete(attempt)
                return 0
            created_at = attempt.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=UTC)
            record = await self.session.get(FileRecordORM, attempt.file_id)
            if created_at > cutoff or record is not None:
                attempt.cleanup_checked_at = now
                return 0
            verdict = await MCPCoreClient().post(
                path='/internal/mcp/cleanup-upload',
                body={
                    'upload_session_id': session_id,
                    'file_id': attempt.file_id,
                    'account_id': attempt.account_id,
                    'user_id': attempt.user_id,
                },
            )
            if verdict.get('eligible') is not True:
                attempt.cleanup_checked_at = now
                return 0
            # The session lock excludes storage writers while core fences
            # all later callbacks and jobs. Check again before external delete.
            if await self.session.get(
                MCPUploadORM, session_id, populate_existing=True
            ):
                return 0
            bucket, path = self.storage.get_storage_path(
                account_id=attempt.account_id, file_id=attempt.file_id
            )
            await self.storage.delete_file(bucket_name=bucket, file_path=path)
            await self.session.delete(attempt)
        return 1

    async def execute(self, limit: int = 100) -> dict[str, int]:
        """Bound a cleanup pass by candidate count and one minute wall time."""
        limit = max(1, min(limit, 100))
        try:
            async with asyncio.timeout(60):
                now = datetime.now(UTC)
                cutoff = now - CLEANUP_MIN_AGE
                async with self.session.begin():
                    attempts = (
                        await self.session.scalars(
                            select(MCPUploadAttemptORM.session_id)
                            .where(
                                MCPUploadAttemptORM.created_at <= cutoff,
                                or_(
                                    MCPUploadAttemptORM.cleanup_checked_at.is_(
                                        None
                                    ),
                                    MCPUploadAttemptORM.cleanup_checked_at
                                    <= now - CLEANUP_RECHECK_INTERVAL,
                                ),
                            )
                            .order_by(
                                nulls_first(
                                    MCPUploadAttemptORM.cleanup_checked_at.asc(),
                                ),
                                MCPUploadAttemptORM.created_at,
                            )
                            .limit(limit)
                        )
                    ).all()
                    candidates = (
                        await self.session.scalars(
                            select(MCPUploadORM.session_id)
                            .join(
                                FileRecordORM,
                                MCPUploadORM.file_id == FileRecordORM.file_id,
                            )
                            .where(
                                FileRecordORM.created_at <= cutoff,
                                FileRecordORM.account_id
                                == MCPUploadORM.account_id,
                                FileRecordORM.user_id == MCPUploadORM.user_id,
                                or_(
                                    MCPUploadORM.cleanup_checked_at.is_(None),
                                    MCPUploadORM.cleanup_checked_at
                                    <= now - CLEANUP_RECHECK_INTERVAL,
                                ),
                            )
                            .order_by(
                                nulls_first(
                                    MCPUploadORM.cleanup_checked_at.asc(),
                                ),
                                FileRecordORM.created_at,
                            )
                            .limit(limit - len(attempts))
                        )
                    ).all()
                deleted = 0
                for session_id in attempts:
                    deleted += await self._cleanup_attempt(
                        session_id=session_id,
                        cutoff=cutoff,
                        now=now,
                    )
                for session_id in candidates:
                    deleted += await self._cleanup_one(
                        session_id=session_id,
                        cutoff=cutoff,
                        now=now,
                    )
                examined = len(attempts) + len(candidates)
                return {
                    'examined': examined,
                    'deleted': deleted,
                    'skipped': examined - deleted,
                }

        except TimeoutError:
            raise MCPCoreUnavailableError from None
