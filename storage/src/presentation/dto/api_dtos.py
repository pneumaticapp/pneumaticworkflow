"""API DTOs."""

from datetime import datetime

from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    """File upload response."""

    public_url: str  # Public URL with unique file identifier
    file_id: str  # Unique file identifier (UUID)


class FileInfoResponse(BaseModel):
    """File information response."""

    id: int
    file_id: str
    filename: str
    size: int
    content_type: str
    user_id: int
    account_id: int
    created_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True
