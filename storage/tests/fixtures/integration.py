from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.shared_kernel.database.base import Base


@pytest_asyncio.fixture(scope='session')
async def test_engine():
    """Create test database engine once per session."""
    database_url = 'sqlite+aiosqlite:///:memory:'
    engine = create_async_engine(database_url, echo=False, future=True)

    # Create tables once
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Close engine at end of session
    await engine.dispose()


@pytest_asyncio.fixture(scope='session')
async def test_session_factory(test_engine):
    """Create session factory once per session."""
    return sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def async_session(
    test_session_factory,
) -> AsyncGenerator[AsyncSession, None]:
    """Create isolated database session for each test."""
    async with test_session_factory() as session:
        yield session
        # Rollback changes after each test
        await session.rollback()

        # Clean all tables after each test
        async with session.begin():
            await session.execute(text('DELETE FROM files'))
            await session.commit()
