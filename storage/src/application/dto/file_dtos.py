from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class UploadFileCommand:
    """Command to upload file"""

    file_content: bytes
    filename: Optional[str]  # Fix
    content_type: Optional[str]  # Fix
    size: int
    user_id: Optional[int]
    account_id: int


@dataclass(frozen=True)
class UploadFileUseCaseResponse:
    """Response for file upload"""

    public_url: str  # Public URL with unique file identifier
    file_id: str  # Unique file identifier (UUID)


@dataclass(frozen=True)
class DownloadFileQuery:
    """Query to download file"""

    file_id: str  # Unique file identifier
    user_id: Optional[int]  # User ID for permission check


@dataclass(frozen=True)
class FileInfoResponse:
    """File information response"""

    id: int
    file_id: str
    filename: str
    size: int
    content_type: str
    user_id: Optional[int]
    account_id: int
    created_at: datetime
