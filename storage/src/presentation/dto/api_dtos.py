"""API DTOs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FileUploadResponse(BaseModel):
    """File upload response."""

    public_url: str = Field(
        description=(
            'Download URL. A valid Files API credential is still required.'
        ),
        examples=[
            'https://example.com/files/12345678-1234-5678-1234-567812345678',
        ],
    )
    file_id: str = Field(
        description='Generated file identifier, usable in Core API fields.',
        examples=['12345678-1234-5678-1234-567812345678'],
    )


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
