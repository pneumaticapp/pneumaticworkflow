from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from src.domain.entities.file_record import FileRecord
from src.infra.repositories.file_record_repository import FileRecordRepository
from src.shared_kernel.database.models import FileRecordORM
from src.shared_kernel.exceptions import (
    DatabaseConnectionError,
    DatabaseConstraintError,
)


class TestFileRecordRepository:
    """Test FileRecordRepository."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self, mock_session):
        """FileRecordRepository instance."""
        return FileRecordRepository(mock_session)

    @pytest.fixture
    def sample_file_record(self):
        """Sample file record."""
        return FileRecord(
            file_id='test-file-id',
            filename='test.txt',
            content_type='text/plain',
            size=1024,
            user_id=1,
            account_id=1,
            created_at=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def sample_file_record_orm(self):
        """Sample file record ORM."""
        return FileRecordORM(
            file_id='test-file-id',
            filename='test.txt',
            content_type='text/plain',
            size=1024,
            user_id=1,
            account_id=1,
            created_at=datetime.now(timezone.utc),
        )

    @pytest.mark.asyncio
    async def test_create__valid_record__ok(
        self,
        repository,
        mock_session,
        sample_file_record,
    ):
        """Test successful file record creation."""
        # Arrange
        mock_session.add = Mock()

        # Act
        await repository.create(sample_file_record)

        # Assert
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create__integrity_error__raise_constraint_error(
        self,
        repository,
        mock_session,
        sample_file_record,
    ):
        """Test file record creation with integrity error."""
        # Arrange
        mock_session.add = Mock(
            side_effect=IntegrityError('UNIQUE constraint failed', None, None),
        )

        # Act & Assert
        with pytest.raises(DatabaseConstraintError):
            await repository.create(sample_file_record)

    @pytest.mark.asyncio
    async def test_create__operational_error__raise_connection_error(
        self,
        repository,
        mock_session,
        sample_file_record,
    ):
        """Test file record creation with operational error."""
        # Arrange
        mock_session.add = Mock(
            side_effect=OperationalError('Connection lost', None, None),
        )

        # Act & Assert
        with pytest.raises(DatabaseConnectionError):
            await repository.create(sample_file_record)

    @pytest.mark.asyncio
    async def test_get_by_id__existing_record__return_record(
        self,
        repository,
        mock_session,
        sample_file_record_orm,
    ):
        """Test successful get by id."""
        # Arrange
        mock_session.execute = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_file_record_orm
        mock_session.execute.return_value = mock_result

        # Act
        result = await repository.get_by_id('test-file-id')

        # Assert
        assert result is not None
        assert result.file_id == 'test-file-id'
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id__non_existent_record__return_none(
        self,
        repository,
        mock_session,
    ):
        """Test get by id when not found."""
        # Arrange
        mock_session.execute = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await repository.get_by_id('non-existent-id')

        # Assert
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id__operational_error__raise_connection_error(
        self,
        repository,
        mock_session,
    ):
        """Test get by id with operational error."""
        # Arrange
        mock_session.execute = AsyncMock(
            side_effect=OperationalError('Connection lost', None, None),
        )

        # Act & Assert
        with pytest.raises(DatabaseConnectionError):
            await repository.get_by_id('test-file-id')
