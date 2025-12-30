from datetime import datetime, timezone

import pytest

from src.domain.entities.file_record import FileRecord
from src.infra.repositories.file_record_repository import FileRecordRepository


class TestFileRecordRepository:
    """Test FileRecordRepository integration."""

    @pytest.mark.asyncio
    async def test_create_and_get__valid_record__return_record(
        self,
        async_session,
    ):
        """Test create and get file record."""
        # Arrange
        repository = FileRecordRepository(async_session)
        file_record = FileRecord(
            file_id='test-file-id-123',
            filename='test_file.txt',
            content_type='text/plain',
            size=1024,
            user_id=1,
            account_id=1,
            created_at=datetime.now(timezone.utc),
        )

        # Act
        await repository.create(file_record)
        await async_session.commit()

        retrieved_record = await repository.get_by_id('test-file-id-123')

        # Assert
        assert retrieved_record is not None
        assert retrieved_record.file_id == 'test-file-id-123'
        assert retrieved_record.filename == 'test_file.txt'
        assert retrieved_record.content_type == 'text/plain'
        assert retrieved_record.size == 1024
        assert retrieved_record.user_id == 1
        assert retrieved_record.account_id == 1

    @pytest.mark.asyncio
    async def test_get__nonexistent_record__return_none(self, async_session):
        """Test get nonexistent file record."""
        # Arrange
        repository = FileRecordRepository(async_session)

        # Act
        retrieved_record = await repository.get_by_id('nonexistent-file-id')

        # Assert
        assert retrieved_record is None
