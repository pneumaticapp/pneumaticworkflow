"""File API endpoints."""

import io
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
from src.domain.entities.file_record import FileRecord
from src.infra.http_client import HttpClient
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
from src.shared_kernel.events.request_events import RequestEventsDep
from src.shared_kernel.exceptions import (
    FileAccessDeniedError,
    FileSizeExceededError,
)
from src.shared_kernel.permissions import is_authenticated
from src.shared_kernel.security import sanitize_content_type

router = APIRouter(prefix='', tags=['files'])

# Pre-compiled patterns for secure_filename
_RE_UNSAFE_CHARS = re.compile(r'[^\w.\- ]', re.UNICODE)
_RE_WHITESPACE = re.compile(r'[\s_]+')
_RE_RANGE = re.compile(r'bytes=(\d+)-(\d*)')


FALLBACK_FILENAME = 'unnamed_file'


def secure_filename(filename: str | None) -> str:
    """Sanitize filename to prevent path traversal and unsafe characters.

    Preserves Unicode letters (Cyrillic, CJK, etc.) while blocking
    control characters, path separators, and shell metacharacters.
    """
    if not filename:
        return FALLBACK_FILENAME
    # Keep Unicode word chars (\w), dot, dash, space
    filename = _RE_UNSAFE_CHARS.sub('_', filename)
    # Collapse multiple spaces/underscores
    filename = _RE_WHITESPACE.sub('_', filename)
    # Prevent hidden files and traversal
    filename = filename.lstrip('._')
    # Strip trailing dots/spaces (Windows FS issue)
    filename = filename.rstrip('. ')
    if not filename:
        return FALLBACK_FILENAME
    return filename


@router.post('/upload', dependencies=[Depends(is_authenticated)])
async def upload_file(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[UploadFileUseCase, Depends(get_upload_use_case)],
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
    events: RequestEventsDep,
) -> FileUploadResponse:
    """Upload file to storage.

    Args:
        file: Uploaded file.
        current_user: Current authenticated user.
        use_case: Upload use case dependency.
        settings: Application settings.
        events: Records of this request for the audit journal.

    Returns:
        FileUploadResponse: Upload result with file ID and public URL.

    """
    # Size without reading the file into memory: seek to the end,
    # ask where that is, rewind.
    file.file.seek(0, io.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > settings.MAX_FILE_SIZE:
        raise FileSizeExceededError(file_size, settings.MAX_FILE_SIZE)

    safe_filename = secure_filename(file.filename)

    command = UploadFileCommand(
        file_stream=file.file,
        filename=safe_filename,
        content_type=sanitize_content_type(file.content_type),
        size=file_size,
        user_id=current_user.user_id,
        account_id=current_user.account_id,
    )

    response = await use_case.execute(command)

    # The record is committed: the file exists, journal it. Awaited
    # and not a background task: what runs after the response depends
    # on the server (a client gone mid-response may skip it or not),
    # and a journal entry has to mean one thing. The wait is bounded
    # by the emit timeout and, past one failure, by the circuit.
    await events.file_upload(
        user=current_user,
        file_id=response.file_id,
        file=command,
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

    if not is_owner:
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

    file_stream = await use_case.get_stream(
        file_record=file_record,
        range_header=range_header,
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
        media_type=file_record.content_type,
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
