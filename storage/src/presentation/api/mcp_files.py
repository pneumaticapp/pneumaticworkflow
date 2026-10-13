"""MCP metadata, revocable downloads and private bounded URL imports."""

# Project convention omits return annotations on procedures.
# mypy: disable-error-code="no-untyped-def"

import secrets
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Path, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.application.dto import DownloadFileQuery
from src.application.use_cases import DownloadFileUseCase
from src.application.use_cases.mcp_cleanup import MCPCleanupService
from src.application.use_cases.mcp_download import MCPDownloadService
from src.application.use_cases.mcp_import import MCPImportService
from src.application.use_cases.mcp_upload import MCPUploadService
from src.domain.entities import FileRecord
from src.infra.http_client import HttpClient
from src.presentation.api.files import download_file
from src.presentation.dto import FileUploadResponse
from src.shared_kernel.auth.dependencies import (
    AuthenticatedUser,
    get_current_user,
)
from src.shared_kernel.auth.mcp import MCPCoreClient
from src.shared_kernel.config import get_settings
from src.shared_kernel.di.container import (
    get_download_use_case,
    get_http_client,
    get_mcp_download_service,
    get_mcp_import_service,
    get_mcp_upload_service,
)
from src.shared_kernel.events.request_events import RequestEventsDep
from src.shared_kernel.exceptions import (
    AuthenticationError,
    DomainFileNotFoundError,
)
from src.shared_kernel.security import sanitize_content_type

router = APIRouter(tags=['MCP Files'])
UserDep = Annotated[AuthenticatedUser, Depends(get_current_user)]
DownloadDep = Annotated[DownloadFileUseCase, Depends(get_download_use_case)]
FileId = Annotated[str, Path(min_length=1, max_length=512)]


def _require_file_service(request: Request):  # noqa: ANN202
    settings = get_settings()
    expected = settings.MCP_FILE_SERVICE_SECRET.get_secret_value()
    authorization = request.headers.get('authorization', '')
    if (
        not settings.MCP_ENABLED
        or not expected
        or not secrets.compare_digest(
            authorization.encode(), f'Bearer {expected}'.encode()
        )
    ):
        raise AuthenticationError(
            details='Core file service authentication required'
        )


def _require_mcp(user: AuthenticatedUser):  # noqa: ANN202
    if not user.mcp_connection_id:
        raise AuthenticationError(details='MCP file delegation is required')


async def _metadata(
    file_id: str,
    user: AuthenticatedUser,
    use_case: DownloadFileUseCase,
) -> FileRecord:
    _require_mcp(user=user)
    record = await use_case.get_metadata(
        query=DownloadFileQuery(file_id=file_id, user_id=user.user_id),
    )
    if record.account_id != user.account_id:
        raise DomainFileNotFoundError(file_id=file_id)
    return record


@router.get('/mcp/files/{file_id}')
async def get_metadata(
    file_id: FileId,
    current_user: UserDep,
    use_case: DownloadDep,
) -> dict[str, Any]:
    """Return attachment metadata after live core permission validation."""
    record = await _metadata(
        file_id=file_id,
        user=current_user,
        use_case=use_case,
    )
    return {
        'file_id': record.file_id,
        'name': record.filename,
        'size': record.size,
        'content_type': sanitize_content_type(record.content_type),
        'created_at': record.created_at.isoformat(),
    }


@router.post('/mcp/files/{file_id}/download-ticket')
async def create_ticket(
    file_id: FileId,
    current_user: UserDep,
    use_case: DownloadDep,
    service: Annotated[MCPDownloadService, Depends(get_mcp_download_service)],
) -> dict[str, Any]:
    """Issue a ticket after live core and attachment metadata validation."""
    record = await _metadata(
        file_id=file_id, user=current_user, use_case=use_case
    )
    return await service.issue(file_id=record.file_id, user=current_user)


@router.get('/mcp/download/{ticket}')
async def download_ticket(  # noqa: PLR0913
    ticket: Annotated[str, Path(min_length=43, max_length=43)],
    request: Request,
    service: Annotated[MCPDownloadService, Depends(get_mcp_download_service)],
    use_case: DownloadDep,
    http_client: Annotated[HttpClient, Depends(get_http_client)],
    events: RequestEventsDep,
    range_header: Annotated[str | None, Header(alias='Range')] = None,
) -> StreamingResponse:
    """Recheck revocation and object permissions for every GET and Range."""
    file_id, grant = await service.authorize(ticket=ticket)
    request.state.user = grant.user()
    response = await download_file(
        file_id=file_id,
        current_user=AuthenticatedUser(auth_user=request.state.user),
        use_case=use_case,
        http_client=http_client,
        events=events,
        range_header=range_header,
    )
    response.headers.update(
        {'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'}
    )
    return response


class ImportRequest(BaseModel):
    """A durable core job supplies its session-bound credential."""

    credential: str = Field(min_length=1, max_length=2048, repr=False)
    upload_session_id: str = Field(min_length=1, max_length=128)
    url: str = Field(min_length=1, max_length=8192, repr=False)
    filename: str = Field(default='imported_file', max_length=512)


@router.post('/internal/mcp/import')
async def import_file(
    body: ImportRequest,
    request: Request,
    events: RequestEventsDep,
    service: Annotated[MCPImportService, Depends(get_mcp_import_service)],
) -> FileUploadResponse:
    """Import only for core workers, then reconcile the durable session map."""
    _require_file_service(request=request)
    grant = await MCPCoreClient().validate(
        credential=body.credential,
        operation='import',
        upload_session_id=body.upload_session_id,
    )
    user = AuthenticatedUser(auth_user=grant.user(credential=body.credential))
    request.state.user = user
    response = await service.execute(
        url=body.url,
        filename=body.filename,
        user=user,
        events=events,
    )
    return FileUploadResponse(
        file_id=response.file_id, public_url=response.public_url
    )


class CleanupRequest(BaseModel):
    """Limit an hourly core-driven cleanup pass."""

    limit: int = Field(default=100, ge=1, le=100)


@router.post('/internal/mcp/cleanup')
async def cleanup_uploads(
    request: Request,
    service: Annotated[MCPUploadService, Depends(get_mcp_upload_service)],
    body: CleanupRequest | None = None,
) -> dict[str, int]:
    """Remove aged, unreferenced uploads only after live core authorization."""
    _require_file_service(request=request)
    return await MCPCleanupService(
        session=service.session,
        storage=service.storage,
    ).execute(
        limit=body.limit if body else 100,
    )
