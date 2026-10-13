"""File API endpoints."""

import re
import urllib.parse
from dataclasses import dataclass
from http import HTTPStatus
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    Path,
    UploadFile,
)
from fastapi.responses import StreamingResponse

from src.application.dto import (
    DownloadFileQuery,
    UploadFileCommand,
)
from src.application.use_cases import (
    DownloadFileUseCase,
    UploadFileUseCase,
)
from src.application.use_cases.mcp_upload import MCPUploadService
from src.domain.entities.file_record import FileRecord
from src.infra.http_client import HttpClient
from src.infra.url_importer import MAX_IMPORT_BYTES
from src.presentation.dto import FileUploadResponse
from src.shared_kernel.auth.dependencies import (
    AuthenticatedUser,
    get_current_user,
)
from src.shared_kernel.config import BaseAppSettings
from src.shared_kernel.di import (
    get_download_use_case,
    get_http_client,
    get_settings_dep,
    get_upload_use_case,
)
from src.shared_kernel.di.container import get_mcp_upload_service
from src.shared_kernel.events.request_events import RequestEventsDep
from src.shared_kernel.exceptions import (
    DomainFileNotFoundError,
    FileAccessDeniedError,
    FileSizeExceededError,
)
from src.shared_kernel.permissions import is_authenticated
from src.shared_kernel.security import sanitize_content_type
from src.shared_kernel.security.filename import (
    FALLBACK_FILENAME,
    secure_filename,
)

router = APIRouter(prefix='', tags=['Files'])

# Pre-compiled byte range pattern.
_RE_RANGE = re.compile(r'bytes=(\d+)-(\d*)')


@router.post('/upload', dependencies=[Depends(is_authenticated)])
async def upload_file(  # noqa: PLR0913
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[UploadFileUseCase, Depends(get_upload_use_case)],
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
    events: RequestEventsDep,
    mcp_upload: Annotated[MCPUploadService, Depends(get_mcp_upload_service)],
) -> FileUploadResponse:
    """Upload file to storage.

    Args:
        file: Uploaded file.
        current_user: Current authenticated user.
        use_case: Upload use case dependency.
        settings: Application settings.
        events: Records of this request for the audit journal.
        mcp_upload: Transactional session upload and core completion.

    Returns:
        FileUploadResponse: Upload result with file ID and public URL.

    """
    # Compute size efficiently without reading into memory
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    size_limit = settings.MAX_FILE_SIZE
    if current_user.mcp_connection_id:
        size_limit = min(
            size_limit,
            settings.MCP_MAX_IMPORT_BYTES,
            MAX_IMPORT_BYTES,
        )
    if file_size > size_limit:
        raise FileSizeExceededError(file_size, size_limit)

    # Sanitize filename
    safe_filename = secure_filename(file.filename or '')

    # Create command
    command = UploadFileCommand(
        file_stream=file.file,
        filename=safe_filename,
        content_type=sanitize_content_type(file.content_type),
        size=file_size,
        user_id=current_user.user_id,
        account_id=current_user.account_id,
    )

    # Execute command
    created = True
    if current_user.mcp_connection_id:
        response, created = await mcp_upload.execute(
            command=command,
            user=current_user,
        )
    else:
        response = await use_case.execute(command)

    # The record is committed: the file exists, journal it. Awaited
    # and not a background task: what runs after the response depends
    # on the server (a client gone mid-response may skip it or not),
    # and a journal entry has to mean one thing. The wait is bounded
    # by the emit timeout and, past one failure, by the circuit.
    if created:
        await events.file_upload(
            user=current_user,
            file_id=response.file_id,
            file=command,
        )
    if current_user.mcp_connection_id:
        await mcp_upload.complete(
            file=command,
            user=current_user,
            file_id=response.file_id,
        )
    return FileUploadResponse(
        public_url=response.public_url,
        file_id=response.file_id,
    )


@router.get('/{file_id}', dependencies=[Depends(is_authenticated)])
async def download_file(  # noqa: PLR0913
    file_id: Annotated[str, Path(min_length=1, max_length=512)],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[DownloadFileUseCase, Depends(get_download_use_case)],
    http_client: Annotated[HttpClient, Depends(get_http_client)],
    events: RequestEventsDep,
    range_header: Annotated[str | None, Header(alias='Range')] = None,
) -> StreamingResponse:
    """Download file from storage.

    Args:
        file_id: File identifier.
        current_user: Current authenticated user.
        use_case: Download use case dependency.
        http_client: HTTP client for permission checks.
        events: Records of this request for the audit journal.
        range_header: Optional HTTP Range header.

    Returns:
        StreamingResponse: File stream with appropriate headers.

    Raises:
        FileAccessDeniedError: If access is denied.

    """
    query = DownloadFileQuery(
        file_id=file_id,
        user_id=current_user.user_id,
        range_header=range_header,
    )

    # Get file metadata first (fail fast, without loading the stream)
    file_record = await use_case.get_metadata(query)

    # Check file owner (optimization: owner always has access)
    is_owner = _check_file_ownership(current_user, file_record)

    if current_user.mcp_connection_id and (
        current_user.account_id != file_record.account_id
    ):
        await events.file_access_denied(
            user=current_user,
            file_record=file_record,
        )
        raise DomainFileNotFoundError(file_id=file_id)

    if not is_owner and not current_user.mcp_connection_id:
        # Check permissions only for non-owners (saves backend request)
        has_access = await http_client.check_file_permission(
            user=current_user,
            file_id=file_id,
        )
        if not has_access:
            await events.file_access_denied(
                user=current_user,
                file_record=file_record,
            )
            raise FileAccessDeniedError(file_id, current_user.user_id)

    # Load the file stream only if access is granted
    file_stream = await use_case.get_stream(
        file_record=file_record,
        range_header=range_header,
    )

    plan = _plan_response(
        file_record=file_record,
        range_header=range_header,
    )
    if plan.status_code == HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE:
        return StreamingResponse(
            iter([b'']),
            status_code=HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE,
            headers=plan.headers,
        )

    if plan.is_from_start:
        await events.file_download(
            user=current_user,
            file_record=file_record,
            is_owner=is_owner,
        )

    return StreamingResponse(
        file_stream,
        status_code=plan.status_code,
        media_type=(
            sanitize_content_type(file_record.content_type)
            if current_user.mcp_connection_id
            else file_record.content_type
        ),
        headers=plan.headers,
    )


def _check_file_ownership(
    current_user: AuthenticatedUser,
    file_record: FileRecord,
) -> bool:
    """Check if current user owns the file."""
    if current_user.user_id is not None:
        return file_record.user_id == current_user.user_id
    # Public/Guest tokens can access files uploaded by Public/Guest
    # tokens (user_id=None) in the same account
    return (
        file_record.user_id is None
        and file_record.account_id == current_user.account_id
    )


@dataclass(frozen=True)
class RangePlan:
    """Status, headers and the first byte of a download response."""

    status_code: HTTPStatus
    headers: dict[str, str]
    start: int = 0

    @property
    def is_from_start(self) -> bool:
        """Whether the response begins with the first byte of the file.

        Only such a response is journaled as a download: a client
        resuming a transfer asks for the rest of the same file again.
        """
        return self.start == 0


def _plan_response(
    file_record: FileRecord,
    range_header: str | None,
) -> RangePlan:
    """Build status code, response headers and start for a download."""
    quoted_filename = urllib.parse.quote(
        file_record.filename or FALLBACK_FILENAME
    )
    headers = {
        'Content-Disposition': (
            f"attachment; filename*=utf-8''{quoted_filename}"
        ),
        'Accept-Ranges': 'bytes',
        'X-Content-Type-Options': 'nosniff',
    }
    total_size = file_record.size

    if not range_header:
        headers['Content-Length'] = str(total_size)
        return RangePlan(status_code=HTTPStatus.OK, headers=headers)

    range_match = _RE_RANGE.match(range_header)
    if not range_match:
        headers['Content-Length'] = str(total_size)
        return RangePlan(status_code=HTTPStatus.OK, headers=headers)

    start = int(range_match.group(1))
    end = int(range_match.group(2)) if range_match.group(2) else total_size - 1
    end = min(end, total_size - 1)
    if start > total_size - 1 or start > end:
        return RangePlan(
            status_code=HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE,
            headers={'Content-Range': f'bytes */{total_size}'},
        )

    content_length = end - start + 1
    headers['Content-Range'] = f'bytes {start}-{end}/{total_size}'
    headers['Content-Length'] = str(content_length)
    return RangePlan(
        status_code=HTTPStatus.PARTIAL_CONTENT,
        headers=headers,
        start=start,
    )
