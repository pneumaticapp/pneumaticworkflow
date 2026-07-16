"""Tests for FileRecordRepository."""

from unittest.mock import ANY, AsyncMock, Mock

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from src.shared_kernel.exceptions import (
    DatabaseConnectionError,
    DatabaseConstraintError,
)


@pytest.mark.asyncio
async def test_create__valid_record__ok(
    file_record_repository,
    repo_mock_session,
    sample_file_record,
):
    # arrange
    repo_mock_session.add = Mock()

    # act
    await file_record_repository.create(
        file_record=sample_file_record,
    )

    # assert
    repo_mock_session.add.assert_called_once_with(ANY)


@pytest.mark.asyncio
async def test_create__integrity_error__raise_constraint(
    file_record_repository,
    repo_mock_session,
    sample_file_record,
):
    # arrange
    repo_mock_session.add = Mock(
        side_effect=IntegrityError(
            'UNIQUE constraint failed',
            None,
            None,
        ),
    )

    # act
    with pytest.raises(DatabaseConstraintError):
        await file_record_repository.create(
            file_record=sample_file_record,
        )


@pytest.mark.asyncio
async def test_create__operational_error__raise_conn_err(
    file_record_repository,
    repo_mock_session,
    sample_file_record,
):
    # arrange
    repo_mock_session.add = Mock(
        side_effect=OperationalError(
            'Connection lost',
            None,
            None,
        ),
    )

    # act
    with pytest.raises(DatabaseConnectionError):
        await file_record_repository.create(
            file_record=sample_file_record,
        )


@pytest.mark.asyncio
async def test_get_by_id__existing__return_record(
    file_record_repository,
    repo_mock_session,
    sample_file_record_orm,
):
    # arrange
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = sample_file_record_orm
    repo_mock_session.execute = AsyncMock(
        return_value=mock_result,
    )

    # act
    result = await file_record_repository.get_by_id(
        file_id='12345678-1234-5678-1234-567812345678',
    )

    # assert
    assert result is not None
    assert result.file_id == ('12345678-1234-5678-1234-567812345678')
    repo_mock_session.execute.assert_called_once_with(
        ANY,
    )


@pytest.mark.asyncio
async def test_get_by_id__non_existent__return_none(
    file_record_repository,
    repo_mock_session,
):
    # arrange
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    repo_mock_session.execute = AsyncMock(
        return_value=mock_result,
    )

    # act
    result = await file_record_repository.get_by_id(
        file_id='non-existent-id',
    )

    # assert
    assert result is None
    repo_mock_session.execute.assert_called_once_with(
        ANY,
    )


@pytest.mark.asyncio
async def test_get_by_id__operational_error__raise_conn_err(
    file_record_repository,
    repo_mock_session,
):
    # arrange
    repo_mock_session.execute = AsyncMock(
        side_effect=OperationalError(
            'Connection lost',
            None,
            None,
        ),
    )

    # act
    with pytest.raises(DatabaseConnectionError):
        await file_record_repository.get_by_id(
            file_id='12345678-1234-5678-1234-567812345678',
        )
