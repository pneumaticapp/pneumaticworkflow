"""File API endpoints."""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
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
from src.infra.http_client import HttpClient
from src.presentation.dto import FileUploadResponse
from src.shared_kernel.auth.dependencies import (
    AuthenticatedUser,
    get_current_user,
)
from src.shared_kernel.config import Settings
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
from src.shared_kernel.permissions import (
    authenticated_no_public,
    is_authenticated,
)

router = APIRouter(prefix='', tags=['files'])


@router.post('/upload', dependencies=[Depends(is_authenticated)])
async def upload_file(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[UploadFileUseCase, Depends(get_upload_use_case)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
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
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > settings.MAX_FILE_SIZE:
        raise FileSizeExceededError(file_size, settings.MAX_FILE_SIZE)

    # Create command
    command = UploadFileCommand(
        file_content=file_content,
        filename=file.filename,
        content_type=file.content_type,
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


@router.get('/{file_id}', dependencies=[Depends(authenticated_no_public)])
async def download_file(
    file_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_case: Annotated[DownloadFileUseCase, Depends(get_download_use_case)],
    http_client: Annotated[HttpClient, Depends(get_http_client)],
) -> StreamingResponse:
    """Download file from storage.

    Args:
        file_id: File identifier.
        current_user: Current authenticated user.
        use_case: Download use case dependency.
        http_client: HTTP client for permission checks.

    Returns:
        StreamingResponse: File stream with appropriate headers.

    Raises:
        FileAccessDeniedError: If access is denied.
    """
    query = DownloadFileQuery(
        file_id=file_id,
        user_id=current_user.user_id,
    )

    # Get file metadata first (fail fast, without loading the stream)
    file_record = await use_case.get_metadata(query)

    # Check file owner (optimization: owner always has access)
    is_owner = file_record.user_id == current_user.user_id

    if not is_owner:
        # Check permissions only for non-owners (saves backend request)
        has_access = await http_client.check_file_permission(
            user=current_user,
            file_id=file_id,
        )
        if not has_access:
            raise FileAccessDeniedError(file_id, current_user.user_id)

    # Load the file stream only if access is granted
    file_stream = await use_case.get_stream(query)

    return StreamingResponse(
        file_stream,
        media_type=file_record.content_type,
        headers={
            'Content-Disposition': (
                f'attachment; filename="{file_record.filename}"'
            ),
            'Content-Length': str(file_record.size),
        },
    )
