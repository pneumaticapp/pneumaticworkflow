"""Database base configuration and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.shared_kernel.config import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Base class for all ORM models
class Base(DeclarativeBase):
    """Declarative base for ORM models."""


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except SQLAlchemyError:
            await session.rollback()
            raise
        finally:
            await session.close()
