"""Dependency injection."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases import (
    DownloadFileUseCase,
    UploadFileUseCase,
)
from src.infra.http_client import HttpClient
from src.infra.repositories import FileRecordRepository, StorageService
from src.shared_kernel.config import Settings, get_settings
from src.shared_kernel.database import get_async_session
from src.shared_kernel.uow import UnitOfWork


def get_settings_dep() -> Settings:
    """Get settings."""
    return get_settings()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async for session in get_async_session():
        yield session


async def get_storage_service() -> AsyncGenerator[StorageService, None]:
    """Get storage service."""
    yield StorageService()


async def get_upload_use_case(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
) -> UploadFileUseCase:
    """Get upload use case."""
    file_repository = FileRecordRepository(session=session)
    unit_of_work = UnitOfWork(session=session)

    return UploadFileUseCase(
        file_repository=file_repository,
        storage_service=storage_service,
        unit_of_work=unit_of_work,
        fastapi_base_url=settings.FASTAPI_BASE_URL,
    )


async def get_download_use_case(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
) -> DownloadFileUseCase:
    """Get download use case."""
    file_repository = FileRecordRepository(session=session)

    return DownloadFileUseCase(
        file_repository=file_repository,
        storage_service=storage_service,
    )


async def get_http_client() -> AsyncGenerator[HttpClient, None]:
    """Get HTTP client."""
    settings = get_settings()
    client = HttpClient(base_url=settings.check_permission_url)
    try:
        yield client
    finally:
        await client.close()
