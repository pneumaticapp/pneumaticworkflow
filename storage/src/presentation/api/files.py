"""File API endpoints."""

import re
import urllib.parse
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


def secure_filename(filename: str | None) -> str:
    """Sanitize filename to prevent path traversal and unsafe characters.

    Preserves Unicode letters (Cyrillic, CJK, etc.) while blocking
    control characters, path separators, and shell metacharacters.
    """
    if not filename:
        return 'unnamed_file'
    # Keep Unicode word chars (\w), dot, dash, space
    filename = _RE_UNSAFE_CHARS.sub('_', filename)
    # Collapse multiple spaces/underscores
    filename = _RE_WHITESPACE.sub('_', filename)
    # Prevent hidden files and traversal
    filename = filename.lstrip('._')
    # Strip trailing dots/spaces (Windows FS issue)
    filename = filename.rstrip('. ')
    if not filename:
        return 'unnamed_file'
    return filename


@router.post('/upload', dependencies=[Depends(is_authenticated)])
async def upload_file(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[UploadFileUseCase, Depends(get_upload_use_case)],
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
) -> FileUploadResponse:
    """Upload file to storage.

    Args:
        file: Uploaded file.
        current_user: Current authenticated user.
        use_case: Upload use case dependency.
        settings: Application settings.

    Returns:
        FileUploadResponse: Upload result with file ID and public URL.

    """
    # Compute size efficiently without reading into memory
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > settings.MAX_FILE_SIZE:
        raise FileSizeExceededError(file_size, settings.MAX_FILE_SIZE)

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
    response = await use_case.execute(command)
    return FileUploadResponse(
        public_url=response.public_url,
        file_id=response.file_id,
    )


@router.get('/{file_id}', dependencies=[Depends(is_authenticated)])
async def download_file(
    file_id: Annotated[str, Path(min_length=1, max_length=512)],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[DownloadFileUseCase, Depends(get_download_use_case)],
    http_client: Annotated[HttpClient, Depends(get_http_client)],
    range_header: Annotated[str | None, Header(alias='Range')] = None,
) -> StreamingResponse:
    """Download file from storage.

    Args:
        file_id: File identifier.
        current_user: Current authenticated user.
        use_case: Download use case dependency.
        http_client: HTTP client for permission checks.
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
            raise FileAccessDeniedError(file_id, current_user.user_id)

    # Load the file stream only if access is granted
    file_stream = await use_case.get_stream(
        file_record=file_record,
        range_header=range_header,
    )

    status_code, headers = _build_response_headers(
        file_record=file_record,
        range_header=range_header,
    )
    if status_code == HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE:
        return StreamingResponse(
            iter([b'']),
            status_code=HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE,
            headers=headers,
        )

    return StreamingResponse(
        file_stream,
        status_code=status_code,
        media_type=file_record.content_type,
        headers=headers,
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


def _build_response_headers(
    file_record: FileRecord,
    range_header: str | None,
) -> tuple[int, dict[str, str]]:
    """Build status code and response headers for file download."""
    quoted_filename = urllib.parse.quote(
        file_record.filename or 'unnamed_file'
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
        return 200, headers

    range_match = _RE_RANGE.match(range_header)
    if not range_match:
        headers['Content-Length'] = str(total_size)
        return 200, headers

    start = int(range_match.group(1))
    end = int(range_match.group(2)) if range_match.group(2) else total_size - 1
    end = min(end, total_size - 1)
    if start > total_size - 1 or start > end:
        return (
            HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE,
            {'Content-Range': f'bytes */{total_size}'},
        )

    content_length = end - start + 1
    headers['Content-Range'] = f'bytes {start}-{end}/{total_size}'
    headers['Content-Length'] = str(content_length)
    return 206, headers
