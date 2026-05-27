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

    def __post_init__(self) -> None:
        """Validate entity invariants (Rich Domain Model)."""
        if self.size < 0:
            raise ValueError(
                f'File size must be non-negative, got {self.size}',
            )
        if not self.file_id:
            raise ValueError('file_id must not be empty')
