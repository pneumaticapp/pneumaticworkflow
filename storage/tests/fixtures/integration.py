import asyncio
import os
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema

from src.application.use_cases.mcp_upload import MCPUploadService
from src.shared_kernel.database.base import Base
from src.shared_kernel.middleware.auth_middleware import AuthUser


@pytest_asyncio.fixture(scope='session')
async def test_engine():
    """Create test database engine once per session."""
    database_url = 'sqlite+aiosqlite:///:memory:'
    engine = create_async_engine(
        database_url,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

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
        await session.rollback()

        async with session.begin():
            await session.execute(
                text('DELETE FROM files'),
            )


@pytest_asyncio.fixture
async def postgres_factory():
    url = os.getenv('MCP_TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set MCP_TEST_DATABASE_URL for isolated PostgreSQL checks')
    schema = 'storage_mcp_test_' + uuid4().hex
    engine = create_async_engine(
        url,
        execution_options={
            'schema_translate_map': {None: schema},
        },
    )
    async with engine.begin() as connection:
        await connection.execute(CreateSchema(schema))
        await connection.run_sync(Base.metadata.create_all)
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        async with engine.begin() as connection:
            await connection.execute(DropSchema(schema, cascade=True))
        await engine.dispose()


@pytest.fixture
def delayed_cleanup() -> tuple[
    type[MCPUploadService], asyncio.Event, asyncio.Event
]:
    first_cleanup, winner_done = asyncio.Event(), asyncio.Event()

    class DelayedCleanup(MCPUploadService):
        async def _cleanup_failed_upload(self, user: AuthUser, file_id: str):
            first_cleanup.set()
            await winner_done.wait()
            await super()._cleanup_failed_upload(user=user, file_id=file_id)

    return DelayedCleanup, first_cleanup, winner_done
