from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class FileRecord:
    """File record entity"""

    file_id: str
    size: int
    content_type: Optional[str]  # Fix
    filename: Optional[str]  # Fix
    user_id: Optional[int]
    account_id: int
    created_at: datetime
