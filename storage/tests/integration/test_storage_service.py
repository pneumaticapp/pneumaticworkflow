"""Tests for StorageService integration."""

from unittest.mock import AsyncMock, Mock

import pytest

from src.infra.adapters.storage_service import (
    StorageService,
)


def test_get_storage_path__valid_account__return_pair():
    # arrange
    service = StorageService()

    # act
    bucket_name, file_path = service.get_storage_path(
        account_id=1,
        file_id=('12345678-1234-5678-1234-567812345678'),
    )

    # assert
    assert '1' in bucket_name
    assert file_path == ('12345678-1234-5678-1234-567812345678')


@pytest.mark.asyncio
async def test_upload__valid_data__ok(
    mock_aioboto3_session,
):
    # arrange
    service = StorageService()
    mock_s3_client = AsyncMock()
    (
        mock_aioboto3_session.return_value.client.return_value.__aenter__
    ).return_value = mock_s3_client

    # act
    await service.upload_file(
        bucket_name='test-bucket',
        file_path='test-file.txt',
        file_stream=b'test content',
        content_type='text/plain',
    )

    # assert
    mock_s3_client.upload_fileobj.assert_called_once_with(
        Fileobj=b'test content',
        Bucket='test-bucket',
        Key='test-file.txt',
        ExtraArgs={'ContentType': 'text/plain'},
    )


@pytest.mark.asyncio
async def test_download__valid_file__return_content(
    mock_aioboto3_session,
):
    # arrange
    service = StorageService()
    mock_s3_client = AsyncMock()

    async def mock_iter_chunks(chunk_size=None):
        yield b'test content'

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
    content = b''
    stream = await service.download_file(
        bucket_name='test-bucket',
        file_path='test-file.txt',
    )
    async for chunk in stream:
        content += chunk

    # assert
    assert content == b'test content'
    mock_s3_client.get_object.assert_called_once_with(
        Bucket='test-bucket',
        Key='test-file.txt',
    )


@pytest.mark.asyncio
async def test_download__chunked__return_all_chunks(
    mock_aioboto3_session,
):
    # arrange
    service = StorageService()
    mock_s3_client = AsyncMock()

    async def mock_iter_chunks(chunk_size=None):
        yield b'chunk1'
        yield b'chunk2'

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
    stream = await service.download_file(
        bucket_name='test-bucket',
        file_path='large-file.txt',
    )
    chunks = [chunk async for chunk in stream]

    # assert
    assert chunks == [b'chunk1', b'chunk2']
    mock_s3_client.get_object.assert_called_once_with(
        Bucket='test-bucket',
        Key='large-file.txt',
    )
