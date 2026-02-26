"""Database ORM models."""

from sqlalchemy import BigInteger, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from .base import Base


class FileRecordORM(Base):
    """File record ORM model."""

    __tablename__ = 'files'

    file_id = Column(
        String,
        primary_key=True,
        unique=True,
        nullable=False,
        index=True,
    )
    size = Column(BigInteger, nullable=False)
    content_type = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    user_id = Column(Integer, nullable=True, index=True)
    account_id = Column(Integer, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
