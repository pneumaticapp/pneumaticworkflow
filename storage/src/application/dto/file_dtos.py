"""Application DTOs for file operations."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UploadFileCommand:
    """Command to upload file."""

    file_content: bytes
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


@dataclass(frozen=True)
class FileInfoResponse:
    """File information response."""

    id: int
    file_id: str
    filename: str
    size: int
    content_type: str
    user_id: int | None
    account_id: int
    created_at: datetime
