"""API DTOs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileUploadResponse(BaseModel):
    """File upload response."""

    public_url: str  # Public URL with unique file identifier
    file_id: str  # Unique file identifier (UUID)


class FileInfoResponse(BaseModel):
    """File information response."""

    model_config = ConfigDict(from_attributes=True)

    file_id: str
    filename: str
    size: int
    content_type: str
    user_id: int | None
    account_id: int
    created_at: datetime
