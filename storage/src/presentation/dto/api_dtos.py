"""API DTOs."""

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict

FIRST_BYTE = 0


class FileUploadResponse(BaseModel):
    """File upload response."""

    public_url: str  # Public URL with unique file identifier
    file_id: str  # Unique file identifier (UUID)


class FileInfoResponse(BaseModel):
    """File information response."""

    model_config = ConfigDict(from_attributes=True)

    file_id: str
    filename: str | None = None
    size: int
    content_type: str | None = None
    user_id: int | None
    account_id: int
    created_at: datetime


@dataclass(frozen=True)
class RangePlan:
    """Status, headers and the first byte of a download response."""

    status_code: int
    headers: dict[str, str]
    start: int = FIRST_BYTE
