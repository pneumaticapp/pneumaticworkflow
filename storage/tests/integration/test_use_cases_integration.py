"""Tests for use cases integration."""

import io
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from src.application.dto.file_dtos import (
    DownloadFileQuery,
    UploadFileCommand,
)
from src.application.use_cases.file_download import (
    DownloadFileUseCase,
)
from src.application.use_cases.file_upload import (
    UploadFileUseCase,
)
from src.domain.entities.file_record import FileRecord
from src.infra.adapters.storage_service import (
    StorageService,
)
from src.infra.repositories.file_record_repository import (
    FileRecordRepository,
)
from src.shared_kernel.exceptions import (
    DomainFileNotFoundError,
)
from src.shared_kernel.uow import UnitOfWork

# --- UploadFileUseCase ---


@pytest.mark.asyncio
async def test_upload__full_integration__ok(
    async_session,
    mock_aioboto3_session,
):
    # arrange
    repository = FileRecordRepository(
        session=async_session,
    )
    storage_service = StorageService()
    unit_of_work = UnitOfWork(session=async_session)
    use_case = UploadFileUseCase(
        file_repository=repository,
        storage_service=storage_service,
        unit_of_work=unit_of_work,
        fastapi_base_url='http://localhost:8000',
    )
    command = UploadFileCommand(
        file_stream=io.BytesIO(b'test file content'),
        filename='test_file.txt',
        content_type='text/plain',
        size=17,
        user_id=1,
        account_id=1,
    )
    mock_s3_client = AsyncMock()
    (
        mock_aioboto3_session.return_value.client.return_value.__aenter__
    ).return_value = mock_s3_client

    # act
    result = await use_case.execute(command=command)

    # assert
    assert result is not None
    assert result.file_id is not None
    assert result.public_url is not None
    assert result.public_url.startswith(
        'http://localhost:8000/',
    )

    await async_session.commit()
    file_record = await repository.get_by_id(
        file_id=result.file_id,
    )
    assert file_record is not None
    assert file_record.filename == 'test_file.txt'
    assert file_record.content_type == 'text/plain'
    assert file_record.size == 17
    assert file_record.user_id == 1
    assert file_record.account_id == 1


@pytest.mark.parametrize(
    ('content_type', 'filename', 'content'),
    [
        (
            'text/plain',
            'document.txt',
            b'This is a text file',
        ),
        (
            'image/png',
            'image.png',
            b'\x89PNG\r\n\x1a\n' + b'x' * 1000,
        ),
        (
            'application/pdf',
            'document.pdf',
            b'%PDF-1.4\n' + b'x' * 2000,
        ),
        (
            'application/json',
            'data.json',
            b'{"key": "value", "number": 42}',
        ),
    ],
)
@pytest.mark.asyncio
async def test_upload__diff_types__ok(
    content_type,
    filename,
    content,
    async_session,
    mock_aioboto3_session,
):
    # arrange
    repository = FileRecordRepository(
        session=async_session,
    )
    storage_service = StorageService()
    unit_of_work = UnitOfWork(session=async_session)
    use_case = UploadFileUseCase(
        file_repository=repository,
        storage_service=storage_service,
        unit_of_work=unit_of_work,
        fastapi_base_url='http://localhost:8000',
    )
    command = UploadFileCommand(
        file_stream=io.BytesIO(content),
        filename=filename,
        content_type=content_type,
        size=len(content),
        user_id=1,
        account_id=1,
    )
    mock_s3_client = AsyncMock()
    (
        mock_aioboto3_session.return_value.client.return_value.__aenter__
    ).return_value = mock_s3_client

    # act
    result = await use_case.execute(command=command)

    # assert
    assert result is not None
    assert result.file_id is not None
    assert result.public_url is not None

    await async_session.commit()
    file_record = await repository.get_by_id(
        file_id=result.file_id,
    )
    assert file_record is not None
    assert file_record.filename == filename
    assert file_record.content_type == content_type
    assert file_record.size == len(content)


# --- DownloadFileUseCase ---


@pytest.mark.asyncio
async def test_download__full_integration__ok(
    async_session,
    mock_aioboto3_session,
):
    # arrange
    repository = FileRecordRepository(
        session=async_session,
    )
    storage_service = StorageService()
    use_case = DownloadFileUseCase(
        file_repository=repository,
        storage_service=storage_service,
    )
    file_record = FileRecord(
        file_id=('12345678-1234-5678-1234-567812345678'),
        filename='test_file.txt',
        content_type='text/plain',
        size=17,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    await repository.create(file_record=file_record)
    await async_session.commit()

    query = DownloadFileQuery(
        file_id=('12345678-1234-5678-1234-567812345678'),
        user_id=1,
    )
    mock_s3_client = AsyncMock()

    async def mock_iter_chunks(chunk_size=None):
        yield b'test file content'

    mock_body = AsyncMock()
    mock_body.iter_chunks = mock_iter_chunks
    mock_body.close = Mock()
    mock_s3_client.get_object.return_value = {
        'Body': mock_body,
    }
    (
        mock_aioboto3_session.return_value.client.return_value.__aenter__
    ).return_value = mock_s3_client

    # act
    result_record = await use_case.get_metadata(
        query=query,
    )
    result_stream = await use_case.get_stream(
        file_record=result_record,
    )

    # assert
    assert result_record is not None
    assert result_record.file_id == ('12345678-1234-5678-1234-567812345678')
    assert result_record.filename == 'test_file.txt'
    assert result_stream is not None

    content = b''
    async for chunk in result_stream:
        content += chunk
    assert content == b'test file content'


@pytest.mark.asyncio
async def test_download__not_found__raise_error(
    async_session,
    mock_aioboto3_session,
):
    # arrange
    repository = FileRecordRepository(
        session=async_session,
    )
    storage_service = StorageService()
    use_case = DownloadFileUseCase(
        file_repository=repository,
        storage_service=storage_service,
    )
    query = DownloadFileQuery(
        file_id=('00000000-0000-0000-0000-000000000000'),
        user_id=1,
    )

    # act & assert
    with pytest.raises(DomainFileNotFoundError):
        await use_case.get_metadata(query=query)
