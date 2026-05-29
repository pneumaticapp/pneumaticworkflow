"""Tests for StorageService and StorageServiceHolder."""

from unittest.mock import AsyncMock

import pytest
from botocore.exceptions import ClientError

from src.infra.repositories.storage_service import (
    StorageService,
    StorageServiceHolder,
)
from src.shared_kernel.exceptions import StorageError


def _make_client_error(code: str) -> ClientError:
    """Create a botocore ClientError with given code."""
    return ClientError(
        error_response={
            'Error': {'Code': code, 'Message': 'test'},
        },
        operation_name='TestOp',
    )


# --- StorageServiceHolder singleton ---


@pytest.mark.asyncio
async def test_holder_get__first_call__creates(
    reset_storage_holder,
    mock_storage_settings,
):

    # act
    instance = await StorageServiceHolder.get()

    # assert
    assert instance is not None
    assert isinstance(instance, StorageService)


@pytest.mark.asyncio
async def test_holder_get__second_call__same(
    reset_storage_holder,
    mock_storage_settings,
):

    # act
    first = await StorageServiceHolder.get()
    second = await StorageServiceHolder.get()

    # assert
    assert first is second


@pytest.mark.asyncio
async def test_holder_close__no_instance__no_error(
    reset_storage_holder,
):

    # act — no exception
    await StorageServiceHolder.close()


@pytest.mark.asyncio
async def test_holder_close__has_instance__sets_none(
    reset_storage_holder,
    mock_storage_settings,
):

    # arrange
    instance = await StorageServiceHolder.get()
    instance.close = AsyncMock()

    # act
    await StorageServiceHolder.close()

    # assert
    instance.close.assert_called_once_with()
    assert StorageServiceHolder._instance is None


@pytest.mark.asyncio
async def test_holder_get__after_close__creates_new(
    reset_storage_holder,
    mock_storage_settings,
):

    # arrange
    first = await StorageServiceHolder.get()
    first.close = AsyncMock()
    await StorageServiceHolder.close()

    # act
    second = await StorageServiceHolder.get()

    # assert
    assert second is not first


# --- StorageService S3 client ---


@pytest.mark.asyncio
async def test_get_client__first_call__creates(
    mock_storage_settings,
):

    # arrange
    service = StorageService()
    mock_client = AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(
        return_value=mock_client,
    )
    service._session.client = lambda **kw: mock_ctx

    # act
    client = await service._get_client()

    # assert
    assert client is mock_client
    mock_ctx.__aenter__.assert_called_once_with()


@pytest.mark.asyncio
async def test_get_client__second_call__reuses(
    mock_storage_settings,
):

    # arrange
    service = StorageService()
    mock_client = AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(
        return_value=mock_client,
    )
    service._session.client = lambda **kw: mock_ctx

    # act
    first = await service._get_client()
    second = await service._get_client()

    # assert
    assert first is second
    mock_ctx.__aenter__.assert_called_once_with()


@pytest.mark.asyncio
async def test_close__with_client__cleans_up(
    mock_storage_settings,
):

    # arrange
    service = StorageService()
    mock_client = AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(
        return_value=mock_client,
    )
    mock_ctx.__aexit__ = AsyncMock(return_value=None)
    service._session.client = lambda **kw: mock_ctx
    await service._get_client()

    # act
    await service.close()

    # assert
    mock_ctx.__aexit__.assert_called_once_with(
        None, None, None,
    )
    assert service._s3_client is None
    assert service._s3_context is None


@pytest.mark.asyncio
async def test_close__no_client__no_error(
    mock_storage_settings,
):

    # arrange
    service = StorageService()

    # act — no exception
    await service.close()


# --- StorageService init ---


def test_init__local__seaweedfs_params(mocker):

    # arrange
    ms = mocker.patch(
        'src.infra.repositories.storage_service.get_settings',
    )
    ms.return_value.STORAGE_TYPE = 'local'
    ms.return_value.BUCKET_PREFIX = 'test'
    ms.return_value.SEAWEEDFS_S3_ENDPOINT = 'http://sw'
    ms.return_value.SEAWEEDFS_S3_ACCESS_KEY = 'ak'
    ms.return_value.SEAWEEDFS_S3_SECRET_KEY = 'sk'
    ms.return_value.SEAWEEDFS_S3_REGION = 'us-east-1'
    ms.return_value.SEAWEEDFS_S3_USE_SSL = False

    # act
    service = StorageService()

    # assert
    assert (
        service._client_params['endpoint_url'] == 'http://sw'
    )
    assert (
        service._client_params['aws_access_key_id'] == 'ak'
    )


def test_init__google__gcs_params(mocker):

    # arrange
    ms = mocker.patch(
        'src.infra.repositories.storage_service.get_settings',
    )
    ms.return_value.STORAGE_TYPE = 'google'
    ms.return_value.BUCKET_PREFIX = 'test'
    ms.return_value.GCS_S3_ENDPOINT = 'https://gcs'
    ms.return_value.GCS_S3_ACCESS_KEY = 'gak'
    ms.return_value.GCS_S3_SECRET_KEY = 'gsk'
    ms.return_value.GCS_S3_REGION = 'us-east-1'

    # act
    service = StorageService()

    # assert
    assert (
        service._client_params['endpoint_url'] == 'https://gcs'
    )
    assert service._config.signature_version == 's3'


def test_init__pool_connections__is_20(
    mock_storage_settings,
):

    # act
    service = StorageService()

    # assert
    assert service._config.max_pool_connections == 20


# --- upload_file ---


@pytest.mark.asyncio
async def test_upload__ok__no_error(
    storage_service_with_mock_s3,
):

    # arrange
    svc, mock_s3 = storage_service_with_mock_s3
    mock_s3.upload_fileobj = AsyncMock()
    stream = AsyncMock()

    # act — no exception
    await svc.upload_file('bucket', 'key', stream, 'image/png')

    # assert
    assert mock_s3.upload_fileobj.call_count == 1


@pytest.mark.asyncio
async def test_upload__with_content_type__extra_args(
    storage_service_with_mock_s3,
):

    # arrange
    svc, mock_s3 = storage_service_with_mock_s3
    mock_s3.upload_fileobj = AsyncMock()
    stream = AsyncMock()

    # act
    await svc.upload_file(
        'b', 'k', stream, 'application/pdf',
    )

    # assert
    call_kwargs = mock_s3.upload_fileobj.call_args
    assert call_kwargs.kwargs['ExtraArgs'] == {
        'ContentType': 'application/pdf',
    }


@pytest.mark.asyncio
async def test_upload__no_content_type__empty_extra(
    storage_service_with_mock_s3,
):

    # arrange
    svc, mock_s3 = storage_service_with_mock_s3
    mock_s3.upload_fileobj = AsyncMock()
    stream = AsyncMock()

    # act
    await svc.upload_file('b', 'k', stream, None)

    # assert
    call_kwargs = mock_s3.upload_fileobj.call_args
    assert call_kwargs.kwargs['ExtraArgs'] == {}


@pytest.mark.asyncio
async def test_upload__no_bucket__create_and_retry(
    storage_service_with_mock_s3,
):

    # arrange
    svc, mock_s3 = storage_service_with_mock_s3
    error = _make_client_error('NoSuchBucket')
    mock_s3.upload_fileobj = AsyncMock(
        side_effect=[error, None],
    )
    mock_s3.create_bucket = AsyncMock()
    stream = AsyncMock()

    # act — no exception
    await svc.upload_file('bucket', 'key', stream, None)

    # assert
    mock_s3.create_bucket.assert_called_once_with(
        Bucket='bucket',
    )
    assert mock_s3.upload_fileobj.call_count == 2
    stream.seek.assert_called_once_with(0)


@pytest.mark.asyncio
async def test_upload__bucket_create_fail__raise(
    storage_service_with_mock_s3,
):

    # arrange
    svc, mock_s3 = storage_service_with_mock_s3
    no_bucket = _make_client_error('NoSuchBucket')
    create_err = _make_client_error('AccessDenied')
    mock_s3.upload_fileobj = AsyncMock(
        side_effect=no_bucket,
    )
    mock_s3.create_bucket = AsyncMock(
        side_effect=create_err,
    )
    stream = AsyncMock()

    # act
    with pytest.raises(StorageError) as exc_info:
        await svc.upload_file(
            'bucket', 'key', stream, None,
        )

    # assert
    assert exc_info.value.error_code.code == 'STORAGE_004'


@pytest.mark.asyncio
async def test_upload__access_denied__raise(
    storage_service_with_mock_s3,
):

    # arrange
    svc, mock_s3 = storage_service_with_mock_s3
    error = _make_client_error('AccessDenied')
    mock_s3.upload_fileobj = AsyncMock(side_effect=error)
    stream = AsyncMock()

    # act
    with pytest.raises(StorageError) as exc_info:
        await svc.upload_file(
            'bucket', 'key', stream, None,
        )

    # assert
    assert exc_info.value.error_code.code == 'STORAGE_002'


# --- download_file ---


@pytest.mark.asyncio
async def test_download__no_such_key__not_found(
    storage_service_with_mock_s3,
):

    # arrange
    svc, mock_s3 = storage_service_with_mock_s3
    svc._chunk_size = 1024
    error = _make_client_error('NoSuchKey')
    mock_s3.get_object = AsyncMock(side_effect=error)

    # act
    with pytest.raises(StorageError) as exc_info:
        async for _ in svc.download_file('bucket', 'path'):
            pass

    # assert
    assert exc_info.value.error_code.code == 'STORAGE_005'


@pytest.mark.asyncio
async def test_download__internal_err__raise(
    storage_service_with_mock_s3,
):

    # arrange
    svc, mock_s3 = storage_service_with_mock_s3
    svc._chunk_size = 1024
    error = _make_client_error('InternalError')
    mock_s3.get_object = AsyncMock(side_effect=error)

    # act
    with pytest.raises(StorageError) as exc_info:
        async for _ in svc.download_file('bucket', 'path'):
            pass

    # assert
    assert exc_info.value.error_code.code == 'STORAGE_003'


@pytest.mark.asyncio
async def test_download__with_range__range_in_kwargs(
    storage_service_with_mock_s3,
):

    # arrange
    svc, mock_s3 = storage_service_with_mock_s3
    svc._chunk_size = 1024

    async def _fake_iter(**_kw):
        yield b'chunk'

    mock_body = AsyncMock()
    mock_body.iter_chunks = _fake_iter
    mock_s3.get_object = AsyncMock(
        return_value={'Body': mock_body},
    )

    # act
    chunks = []
    async for chunk in svc.download_file(
        'b', 'k', range_header='bytes=0-100',
    ):
        chunks.append(chunk)

    # assert
    call_kwargs = mock_s3.get_object.call_args.kwargs
    assert call_kwargs['Range'] == 'bytes=0-100'


# --- delete_file ---


@pytest.mark.asyncio
async def test_delete__ok__no_error(
    storage_service_with_mock_s3,
):

    # arrange
    svc, mock_s3 = storage_service_with_mock_s3
    mock_s3.delete_object = AsyncMock()

    # act — no exception
    await svc.delete_file('bucket', 'key')

    # assert
    mock_s3.delete_object.assert_called_once_with(
        Bucket='bucket',
        Key='key',
    )


@pytest.mark.asyncio
async def test_delete__client_error__raise(
    storage_service_with_mock_s3,
):

    # arrange
    svc, mock_s3 = storage_service_with_mock_s3
    error = _make_client_error('InternalError')
    mock_s3.delete_object = AsyncMock(side_effect=error)

    # act
    with pytest.raises(StorageError) as exc_info:
        await svc.delete_file('bucket', 'key')

    # assert
    assert exc_info.value.error_code.code == 'STORAGE_006'
