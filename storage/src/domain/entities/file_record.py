"""Domain entities for file management."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FileRecord:
    """File record entity."""

    file_id: str
    size: int
    content_type: str | None
    filename: str | None
    user_id: int | None
    account_id: int
    created_at: datetime
