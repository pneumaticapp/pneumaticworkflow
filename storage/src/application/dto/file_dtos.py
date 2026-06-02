"""Application DTOs for file operations."""

from dataclasses import dataclass
from typing import IO


@dataclass(frozen=True)
class UploadFileCommand:
    """Command to upload file."""

    file_stream: IO[bytes]
    filename: str | None
    content_type: str | None
    size: int
    user_id: int | None
    account_id: int


@dataclass(frozen=True)
class UploadFileUseCaseResponse:
    """Response for file upload."""

    public_url: str  # Public URL with unique file identifier
    file_id: str  # Unique file identifier (UUID)


@dataclass(frozen=True)
class DownloadFileQuery:
    """Query to download file."""

    file_id: str  # Unique file identifier
    user_id: int | None
    range_header: str | None = None
