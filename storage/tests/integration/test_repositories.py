"""Tests for FileRecordRepository integration."""

from datetime import UTC, datetime

import pytest
from src.domain.entities.file_record import FileRecord
from src.infra.repositories.file_record_repository import (
    FileRecordRepository,
)


@pytest.mark.asyncio
async def test_create_and_get__valid__return_record(
    async_session,
):
    # arrange
    repository = FileRecordRepository(
        session=async_session,
    )
    file_record = FileRecord(
        file_id=('12345678-1234-5678-1234-567812345679'),
        filename='test_file.txt',
        content_type='text/plain',
        size=1024,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )

    # act
    await repository.create(file_record=file_record)
    await async_session.commit()
    retrieved = await repository.get_by_id(
        file_id=('12345678-1234-5678-1234-567812345679'),
    )

    # assert
    assert retrieved is not None
    assert retrieved.file_id == ('12345678-1234-5678-1234-567812345679')
    assert retrieved.filename == 'test_file.txt'
    assert retrieved.content_type == 'text/plain'
    assert retrieved.size == 1024
    assert retrieved.user_id == 1
    assert retrieved.account_id == 1


@pytest.mark.asyncio
async def test_get__nonexistent__return_none(
    async_session,
):
    # arrange
    repository = FileRecordRepository(
        session=async_session,
    )

    # act
    retrieved = await repository.get_by_id(
        file_id=('00000000-0000-0000-0000-000000000000'),
    )

    # assert
    assert retrieved is None
