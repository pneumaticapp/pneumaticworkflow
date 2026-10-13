"""Database ORM models."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class FileRecordORM(Base):
    """File record ORM model."""

    __tablename__ = 'files'

    file_id: Mapped[str] = mapped_column(String, primary_key=True)
    size: Mapped[int] = mapped_column(BigInteger)
    content_type: Mapped[str | None] = mapped_column(String, nullable=True)
    filename: Mapped[str | None] = mapped_column(String, nullable=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, index=True, nullable=True
    )
    account_id: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class MCPUploadORM(Base):
    """One durable file mapping per core upload session."""

    __tablename__ = 'mcp_uploads'
    session_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    connection_id: Mapped[str] = mapped_column(String(128))
    user_id: Mapped[int] = mapped_column(Integer)
    account_id: Mapped[int] = mapped_column(Integer)
    file_id: Mapped[str] = mapped_column(String, unique=True)
    fingerprint: Mapped[str] = mapped_column(String(64))
    cleanup_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )


class MCPUploadAttemptORM(Base):
    """A committed cleanup journal entry exists before any MCP S3 write."""

    __tablename__ = 'mcp_upload_attempts'
    session_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    connection_id: Mapped[str] = mapped_column(String(128))
    user_id: Mapped[int] = mapped_column(Integer)
    account_id: Mapped[int] = mapped_column(Integer)
    file_id: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    cleanup_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )


class MCPDownloadTicketORM(Base):
    """Only a hash of a five-minute bearer ticket is stored."""

    __tablename__ = 'mcp_download_tickets'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    connection_id: Mapped[str] = mapped_column(String(128))
    authorization_id: Mapped[str] = mapped_column(String(128))
    user_id: Mapped[int] = mapped_column(Integer)
    account_id: Mapped[int] = mapped_column(Integer)
    file_id: Mapped[str] = mapped_column(ForeignKey('files.file_id'))
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
