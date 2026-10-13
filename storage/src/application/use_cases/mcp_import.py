"""Bounded URL import with durable upload reconciliation."""

import httpcore

from src.application.dto import UploadFileCommand, UploadFileUseCaseResponse
from src.application.use_cases.mcp_upload import MCPUploadService
from src.infra.url_importer import UnsafeImportError, URLImporter
from src.shared_kernel.auth.dependencies import AuthenticatedUser
from src.shared_kernel.auth.mcp import MCPCoreClient
from src.shared_kernel.config import BaseAppSettings
from src.shared_kernel.events.request_events import RequestEvents
from src.shared_kernel.exceptions import AuthenticationError
from src.shared_kernel.exceptions.mcp_exceptions import MCPImportError
from src.shared_kernel.security import sanitize_content_type
from src.shared_kernel.security.filename import secure_filename


class MCPImportService:
    """Import bytes and acknowledge them only after current core validation."""

    def __init__(
        self, uploads: MCPUploadService, settings: BaseAppSettings
    ) -> None:
        """Bind upload infrastructure and configured import limits."""
        self.uploads = uploads
        self.settings = settings

    async def execute(
        self,
        url: str,
        filename: str,
        user: AuthenticatedUser,
        events: RequestEvents,
    ) -> UploadFileUseCaseResponse:
        """Reconcile a committed file before fetching and storing new bytes."""
        existing = await self.uploads.find_completed(user=user)
        if existing is not None:
            await self.uploads.complete(
                file=existing,
                user=user,
                file_id=existing.file_id,
                operation='import',
            )
            return UploadFileUseCaseResponse(
                file_id=existing.file_id,
                public_url=f'{self.settings.FASTAPI_BASE_URL}/{existing.file_id}',
            )
        try:
            imported = await URLImporter(
                max_bytes=min(
                    self.settings.MCP_MAX_IMPORT_BYTES,
                    self.settings.MAX_FILE_SIZE,
                )
            ).download(raw_url=url)
        except (
            UnsafeImportError,
            httpcore.NetworkError,
            httpcore.ProtocolError,
            httpcore.TimeoutException,
            OSError,
            ValueError,
            TimeoutError,
        ):
            raise MCPImportError from None
        try:
            # The fetch may take a minute: do not store a revoked grant.
            current_grant = await MCPCoreClient().validate(
                credential=user.token,
                operation='import',
                upload_session_id=user.mcp_upload_session_id,
            )
            if (
                current_grant.user_id,
                current_grant.account_id,
                current_grant.connection_id,
            ) != (user.user_id, user.account_id, user.mcp_connection_id):
                raise AuthenticationError(
                    details='Import grant identity changed'
                )
            command = UploadFileCommand(
                file_stream=imported.stream,
                filename=secure_filename(filename=filename),
                content_type=sanitize_content_type(
                    content_type=imported.content_type,
                ),
                size=imported.size,
                user_id=user.user_id,
                account_id=user.account_id,
            )
            response, created = await self.uploads.execute(
                command=command,
                user=user,
                operation='import',
            )
            if created:
                await events.file_upload(
                    user=user, file_id=response.file_id, file=command
                )
            await self.uploads.complete(
                file=command,
                user=user,
                file_id=response.file_id,
                operation='import',
            )
            return UploadFileUseCaseResponse(
                file_id=response.file_id, public_url=response.public_url
            )
        finally:
            imported.stream.close()
