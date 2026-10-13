"""Transactional, session-bound MCP uploads and callback reconciliation."""

# Project convention omits return annotations on procedures.
# mypy: disable-error-code="no-untyped-def"

import asyncio
import hashlib
import logging
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import UploadFileCommand, UploadFileUseCaseResponse
from src.domain.entities import FileRecord
from src.infra.adapters.storage_service import StorageService
from src.infra.mappers import FileRecordMapper
from src.shared_kernel.auth.mcp import MCPCoreClient
from src.shared_kernel.config import BaseAppSettings
from src.shared_kernel.database.models import (
    FileRecordORM,
    MCPUploadAttemptORM,
    MCPUploadORM,
)
from src.shared_kernel.exceptions import PermissionDeniedError
from src.shared_kernel.exceptions.mcp_exceptions import (
    MCPCoreUnavailableError,
    MCPUploadConflictError,
)
from src.shared_kernel.middleware.auth_middleware import AuthUser

logger = logging.getLogger(__name__)


async def lock_upload_session(  # noqa: ANN201
    session: AsyncSession,
    session_id: str,
):
    """Serialize writes and cleanup of the same core session in PostgreSQL."""
    if session.get_bind().dialect.name == 'postgresql':
        key = int.from_bytes(
            hashlib.sha256(session_id.encode()).digest()[:8],
            signed=True,
        )
        await session.execute(
            statement=text('SELECT pg_advisory_xact_lock(:key)'),
            params={'key': key},
        )


def _fingerprint(command: UploadFileCommand) -> str:
    digest = hashlib.sha256()
    digest.update((command.filename or '').encode())
    digest.update(b'\x00')
    digest.update((command.content_type or '').encode())
    digest.update(b'\x00')
    command.file_stream.seek(0)
    while chunk := command.file_stream.read(1024 * 1024):
        digest.update(chunk)
    command.file_stream.seek(0)
    return digest.hexdigest()


class MCPUploadService:
    """Keep the file and session mapping in the same PostgreSQL transaction."""

    def __init__(  # noqa: ANN204
        self,
        session: AsyncSession,
        storage: StorageService,
        settings: BaseAppSettings,
    ):
        """Bind infrastructure dependencies, never request identity."""
        self.session = session
        self.storage = storage
        self.settings = settings

    async def _revalidate(  # noqa: ANN202
        self,
        user: AuthUser,
        operation: str,
    ):
        grant = await MCPCoreClient().validate(
            credential=user.token,
            operation=operation,
            upload_session_id=user.mcp_upload_session_id,
        )
        if (grant.user_id, grant.account_id, grant.connection_id) != (
            user.user_id,
            user.account_id,
            user.mcp_connection_id,
        ):
            raise PermissionDeniedError(
                details='Upload grant identity changed',
            )

    async def _cleanup_failed_upload(  # noqa: ANN202
        self, user: AuthUser, file_id: str
    ):
        if user.account_id is None:
            raise PermissionDeniedError(details='Upload account is required')
        await self.session.rollback()
        async with self.session.begin():
            await lock_upload_session(
                session=self.session,
                session_id=user.mcp_upload_session_id or '',
            )
            # Never erase a committed winner, including lost commit replies.
            if await self.session.get(
                MCPUploadORM, user.mcp_upload_session_id
            ):
                return
            if await self.session.get(FileRecordORM, file_id):
                # A non-MCP record is never evidence of an orphan object.
                return
            bucket, path = self.storage.get_storage_path(
                account_id=user.account_id,
                file_id=file_id,
            )
            await self.storage.delete_file(bucket_name=bucket, file_path=path)
            await self.session.execute(
                delete(MCPUploadAttemptORM).where(
                    MCPUploadAttemptORM.session_id
                    == user.mcp_upload_session_id
                )
            )

    async def _protected_cleanup(  # noqa: ANN202
        self,
        user: AuthUser,
        file_id: str,
    ):
        async def cleanup():  # noqa: ANN202
            try:
                async with asyncio.timeout(60):
                    await self._cleanup_failed_upload(
                        user=user,
                        file_id=file_id,
                    )
            except (Exception, asyncio.CancelledError):  # noqa: BLE001
                logger.warning('MCP upload cleanup failed; journal will retry')

        task = asyncio.create_task(cleanup())  # type: ignore[no-untyped-call]
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                # Finish using the request's DB session before reraising the
                # original failure, even if the caller cancels again.
                continue

    async def _journal_attempt(self, user: AuthUser):  # noqa: ANN202
        async with self.session.begin():
            await lock_upload_session(
                session=self.session,
                session_id=user.mcp_upload_session_id or '',
            )
            if await self.session.get(
                MCPUploadORM, user.mcp_upload_session_id
            ):
                return
            attempt = await self.session.get(
                MCPUploadAttemptORM, user.mcp_upload_session_id
            )
            if attempt is None:
                self.session.add(
                    MCPUploadAttemptORM(
                        session_id=user.mcp_upload_session_id,
                        connection_id=user.mcp_connection_id,
                        user_id=user.user_id,
                        account_id=user.account_id,
                        file_id=str(
                            uuid5(
                                NAMESPACE_URL,
                                f'pneumatic:mcp:{user.mcp_upload_session_id}',
                            )
                        ),
                    )
                )
            elif (
                attempt.connection_id,
                attempt.user_id,
                attempt.account_id,
            ) != (user.mcp_connection_id, user.user_id, user.account_id):
                raise PermissionDeniedError(
                    details='Upload attempt identity mismatch',
                )

    async def _claim(
        self,
        user: AuthUser,
        fingerprint: str,
    ) -> tuple[MCPUploadORM, bool]:
        session_id = user.mcp_upload_session_id
        mapping = await self.session.get(MCPUploadORM, session_id)
        created = False
        if mapping is None:
            file_id = str(uuid5(NAMESPACE_URL, f'pneumatic:mcp:{session_id}'))
            if await self.session.get(FileRecordORM, file_id):
                # Never overwrite a pre-existing file outside this session.
                raise MCPUploadConflictError
            mapping = MCPUploadORM(
                session_id=session_id,
                connection_id=user.mcp_connection_id,
                user_id=user.user_id,
                account_id=user.account_id,
                file_id=file_id,
                fingerprint=fingerprint,
            )
            self.session.add(mapping)
            await self.session.flush()
            created = True
        if (
            mapping.connection_id != user.mcp_connection_id
            or mapping.user_id != user.user_id
            or mapping.account_id != user.account_id
        ):
            raise PermissionDeniedError(
                details='Upload session identity mismatch',
            )
        if mapping.fingerprint != fingerprint:
            raise MCPUploadConflictError
        return mapping, created

    async def _store(  # noqa: ANN202
        self,
        command: UploadFileCommand,
        file_id: str,
    ):
        file_record = FileRecord(
            file_id=file_id,
            filename=command.filename,
            content_type=command.content_type,
            size=command.size,
            user_id=command.user_id,
            account_id=command.account_id,
            created_at=datetime.now(UTC),
        )
        bucket, path = self.storage.get_storage_path(
            account_id=command.account_id,
            file_id=file_id,
        )
        await self.storage.upload_file(
            bucket_name=bucket,
            file_path=path,
            file_stream=command.file_stream,
            content_type=command.content_type,
        )
        self.session.add(FileRecordMapper.entity_to_orm(entity=file_record))
        await self.session.flush()

    async def execute(
        self,
        command: UploadFileCommand,
        user: AuthUser,
        *,
        operation: str = 'upload',
    ) -> tuple[UploadFileUseCaseResponse, bool]:
        """Serialize concurrent uploads by the unique core session key."""
        if (
            not user.mcp_connection_id
            or not user.mcp_upload_session_id
            or user.user_id is None
            or user.account_id is None
            or (command.user_id, command.account_id)
            != (user.user_id, user.account_id)
        ):
            raise PermissionDeniedError(details='Invalid MCP upload identity')
        fingerprint_task = asyncio.create_task(
            asyncio.to_thread(_fingerprint, command=command),
        )
        try:
            fingerprint = await asyncio.shield(fingerprint_task)
        except asyncio.CancelledError:
            # Closing the request stream cannot race a live hashing thread.
            drain = asyncio.gather(fingerprint_task, return_exceptions=True)
            while not drain.done():
                try:
                    await asyncio.shield(drain)
                except asyncio.CancelledError:
                    continue
            raise
        # This transaction must commit before S3: a killed process cannot run
        # exception cleanup, but the hourly core-fenced journal cleanup can.
        await self._journal_attempt(user=user)
        created = False
        file_id = ''
        try:
            async with self.session.begin():
                await lock_upload_session(
                    session=self.session,
                    session_id=user.mcp_upload_session_id,
                )
                mapping, created = await self._claim(
                    user=user,
                    fingerprint=fingerprint,
                )
                file_id = mapping.file_id
                if created:
                    await self._revalidate(user=user, operation=operation)
                    await self._store(command=command, file_id=file_id)
                await self.session.execute(
                    delete(MCPUploadAttemptORM).where(
                        MCPUploadAttemptORM.session_id
                        == user.mcp_upload_session_id
                    )
                )
        except (Exception, asyncio.CancelledError):
            if created and file_id:
                await self._protected_cleanup(user=user, file_id=file_id)
            raise
        response = UploadFileUseCaseResponse(
            file_id=file_id,
            public_url=f'{self.settings.FASTAPI_BASE_URL}/{file_id}',
        )
        return response, created

    async def complete(  # noqa: ANN201
        self,
        file: UploadFileCommand | FileRecord,
        user: AuthUser,
        file_id: str,
        *,
        operation: str = 'upload',
    ):
        """Reconcile a committed upload without trusting a browser file ID."""
        await self._revalidate(user=user, operation=operation)
        result = await MCPCoreClient().post(
            path='/internal/mcp/complete-upload',
            body={
                'credential': user.token,
                'upload_session_id': user.mcp_upload_session_id,
                'file_id': file_id,
                'name': file.filename,
                'size': file.size,
                'content_type': file.content_type,
            },
        )

        if (
            result.get('id') != user.mcp_upload_session_id
            or result.get('file_id') != file_id
            or result.get('status') != 'ready'
        ):
            raise MCPCoreUnavailableError

    async def find_completed(self, user: AuthUser) -> FileRecord | None:
        """Reconcile an import retry before any further external fetch."""
        async with self.session.begin():
            mapping = await self.session.get(
                MCPUploadORM,
                user.mcp_upload_session_id,
            )
            if mapping is None:
                return None
            if (
                mapping.connection_id != user.mcp_connection_id
                or mapping.user_id != user.user_id
                or mapping.account_id != user.account_id
            ):
                raise PermissionDeniedError(
                    details='Upload session identity mismatch',
                )
            record = await self.session.get(FileRecordORM, mapping.file_id)
            if record is None:
                raise MCPCoreUnavailableError
            if (record.user_id, record.account_id) != (
                mapping.user_id,
                mapping.account_id,
            ):
                raise PermissionDeniedError(
                    details='Upload record identity mismatch',
                )
            return FileRecordMapper.orm_to_entity(orm=record)
