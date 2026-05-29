from unittest.mock import AsyncMock, patch

import pytest
from botocore.exceptions import ClientError

from src.infra.repositories.storage_service import (
    StorageService,
    StorageServiceHolder,
)
from src.shared_kernel.exceptions import StorageError


class TestStorageServiceHolder:
    """Tests for StorageServiceHolder singleton pattern."""

    @pytest.fixture(autouse=True)
    def _reset_holder(self):
        """Reset holder state before each test."""
        StorageServiceHolder._instance = None
        yield
        StorageServiceHolder._instance = None

    @patch(
        'src.infra.repositories.storage_service.get_settings',
    )
    async def test_get__first_call__creates_instance(
        self,
        mock_settings,
    ):
        """Test first get() creates new instance."""
        # arrange
        mock_settings.return_value.STORAGE_TYPE = 'local'
        mock_settings.return_value.BUCKET_PREFIX = 'test'
        mock_settings.return_value.SEAWEEDFS_S3_ENDPOINT = 'http://s3'
        mock_settings.return_value.SEAWEEDFS_S3_ACCESS_KEY = 'key'
        mock_settings.return_value.SEAWEEDFS_S3_SECRET_KEY = 'secret'
        mock_settings.return_value.SEAWEEDFS_S3_REGION = 'us-east-1'
        mock_settings.return_value.SEAWEEDFS_S3_USE_SSL = False

        # act
        instance = await StorageServiceHolder.get()

        # assert
        assert instance is not None
        assert isinstance(instance, StorageService)

    @patch(
        'src.infra.repositories.storage_service.get_settings',
    )
    async def test_get__second_call__returns_same(
        self,
        mock_settings,
    ):
        """Test second get() returns same instance."""
        # arrange
        mock_settings.return_value.STORAGE_TYPE = 'local'
        mock_settings.return_value.BUCKET_PREFIX = 'test'
        mock_settings.return_value.SEAWEEDFS_S3_ENDPOINT = 'http://s3'
        mock_settings.return_value.SEAWEEDFS_S3_ACCESS_KEY = 'key'
        mock_settings.return_value.SEAWEEDFS_S3_SECRET_KEY = 'secret'
        mock_settings.return_value.SEAWEEDFS_S3_REGION = 'us-east-1'
        mock_settings.return_value.SEAWEEDFS_S3_USE_SSL = False

        # act
        first = await StorageServiceHolder.get()
        second = await StorageServiceHolder.get()

        # assert
        assert first is second

    async def test_close__no_instance__no_error(self):
        """Test close() without instance does not raise."""
        # act + assert — no exception
        await StorageServiceHolder.close()

    @patch(
        'src.infra.repositories.storage_service.get_settings',
    )
    async def test_close__has_instance__sets_none(
        self,
        mock_settings,
    ):
        """Test close() cleans up instance."""
        # arrange
        mock_settings.return_value.STORAGE_TYPE = 'local'
        mock_settings.return_value.BUCKET_PREFIX = 'test'
        mock_settings.return_value.SEAWEEDFS_S3_ENDPOINT = 'http://s3'
        mock_settings.return_value.SEAWEEDFS_S3_ACCESS_KEY = 'key'
        mock_settings.return_value.SEAWEEDFS_S3_SECRET_KEY = 'secret'
        mock_settings.return_value.SEAWEEDFS_S3_REGION = 'us-east-1'
        mock_settings.return_value.SEAWEEDFS_S3_USE_SSL = False

        instance = await StorageServiceHolder.get()
        instance.close = AsyncMock()

        # act
        await StorageServiceHolder.close()

        # assert
        instance.close.assert_called_once_with()
        assert StorageServiceHolder._instance is None

    @patch(
        'src.infra.repositories.storage_service.get_settings',
    )
    async def test_get__after_close__creates_new(
        self,
        mock_settings,
    ):
        """Test get() after close() creates new instance."""
        # arrange
        mock_settings.return_value.STORAGE_TYPE = 'local'
        mock_settings.return_value.BUCKET_PREFIX = 'test'
        mock_settings.return_value.SEAWEEDFS_S3_ENDPOINT = 'http://s3'
        mock_settings.return_value.SEAWEEDFS_S3_ACCESS_KEY = 'key'
        mock_settings.return_value.SEAWEEDFS_S3_SECRET_KEY = 'secret'
        mock_settings.return_value.SEAWEEDFS_S3_REGION = 'us-east-1'
        mock_settings.return_value.SEAWEEDFS_S3_USE_SSL = False

        first = await StorageServiceHolder.get()
        first.close = AsyncMock()
        await StorageServiceHolder.close()

        # act
        second = await StorageServiceHolder.get()

        # assert
        assert second is not first


class TestStorageServiceClient:
    """Tests for StorageService persistent S3 client."""

    @patch(
        'src.infra.repositories.storage_service.get_settings',
    )
    async def test_get_client__first_call__creates(
        self,
        mock_settings,
    ):
        """Test _get_client creates client on first call."""
        # arrange
        mock_settings.return_value.STORAGE_TYPE = 'local'
        mock_settings.return_value.BUCKET_PREFIX = 'test'
        mock_settings.return_value.SEAWEEDFS_S3_ENDPOINT = 'http://s3'
        mock_settings.return_value.SEAWEEDFS_S3_ACCESS_KEY = 'key'
        mock_settings.return_value.SEAWEEDFS_S3_SECRET_KEY = 'secret'
        mock_settings.return_value.SEAWEEDFS_S3_REGION = 'us-east-1'
        mock_settings.return_value.SEAWEEDFS_S3_USE_SSL = False

        service = StorageService()

        # Mock the session.client context manager
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

    @patch(
        'src.infra.repositories.storage_service.get_settings',
    )
    async def test_get_client__second_call__reuses(
        self,
        mock_settings,
    ):
        """Test _get_client reuses client on second call."""
        # arrange
        mock_settings.return_value.STORAGE_TYPE = 'local'
        mock_settings.return_value.BUCKET_PREFIX = 'test'
        mock_settings.return_value.SEAWEEDFS_S3_ENDPOINT = 'http://s3'
        mock_settings.return_value.SEAWEEDFS_S3_ACCESS_KEY = 'key'
        mock_settings.return_value.SEAWEEDFS_S3_SECRET_KEY = 'secret'
        mock_settings.return_value.SEAWEEDFS_S3_REGION = 'us-east-1'
        mock_settings.return_value.SEAWEEDFS_S3_USE_SSL = False

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
        # __aenter__ called only once (reused)
        mock_ctx.__aenter__.assert_called_once_with()

    @patch(
        'src.infra.repositories.storage_service.get_settings',
    )
    async def test_close__with_client__cleans_up(
        self,
        mock_settings,
    ):
        """Test close() properly exits S3 context manager."""
        # arrange
        mock_settings.return_value.STORAGE_TYPE = 'local'
        mock_settings.return_value.BUCKET_PREFIX = 'test'
        mock_settings.return_value.SEAWEEDFS_S3_ENDPOINT = 'http://s3'
        mock_settings.return_value.SEAWEEDFS_S3_ACCESS_KEY = 'key'
        mock_settings.return_value.SEAWEEDFS_S3_SECRET_KEY = 'secret'
        mock_settings.return_value.SEAWEEDFS_S3_REGION = 'us-east-1'
        mock_settings.return_value.SEAWEEDFS_S3_USE_SSL = False

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

    @patch(
        'src.infra.repositories.storage_service.get_settings',
    )
    async def test_close__no_client__no_error(
        self,
        mock_settings,
    ):
        """Test close() without initialized client is safe."""
        # arrange
        mock_settings.return_value.STORAGE_TYPE = 'local'
        mock_settings.return_value.BUCKET_PREFIX = 'test'
        mock_settings.return_value.SEAWEEDFS_S3_ENDPOINT = 'http://s3'
        mock_settings.return_value.SEAWEEDFS_S3_ACCESS_KEY = 'key'
        mock_settings.return_value.SEAWEEDFS_S3_SECRET_KEY = 'secret'
        mock_settings.return_value.SEAWEEDFS_S3_REGION = 'us-east-1'
        mock_settings.return_value.SEAWEEDFS_S3_USE_SSL = False

        service = StorageService()

        # act + assert — no exception
        await service.close()


class TestStorageServiceInit:
    """Tests for StorageService initialization."""

    @patch(
        'src.infra.repositories.storage_service.get_settings',
    )
    def test_init__local__seaweedfs_params(
        self,
        mock_settings,
    ):
        """Test local storage type uses SeaweedFS params."""
        # arrange
        mock_settings.return_value.STORAGE_TYPE = 'local'
        mock_settings.return_value.BUCKET_PREFIX = 'test'
        mock_settings.return_value.SEAWEEDFS_S3_ENDPOINT = 'http://sw'
        mock_settings.return_value.SEAWEEDFS_S3_ACCESS_KEY = 'ak'
        mock_settings.return_value.SEAWEEDFS_S3_SECRET_KEY = 'sk'
        mock_settings.return_value.SEAWEEDFS_S3_REGION = 'us-east-1'
        mock_settings.return_value.SEAWEEDFS_S3_USE_SSL = False

        # act
        service = StorageService()

        # assert
        assert service._client_params['endpoint_url'] == 'http://sw'
        assert service._client_params['aws_access_key_id'] == 'ak'

    @patch(
        'src.infra.repositories.storage_service.get_settings',
    )
    def test_init__google__gcs_params(
        self,
        mock_settings,
    ):
        """Test google storage type uses GCS params."""
        # arrange
        mock_settings.return_value.STORAGE_TYPE = 'google'
        mock_settings.return_value.BUCKET_PREFIX = 'test'
        mock_settings.return_value.GCS_S3_ENDPOINT = 'https://gcs'
        mock_settings.return_value.GCS_S3_ACCESS_KEY = 'gak'
        mock_settings.return_value.GCS_S3_SECRET_KEY = 'gsk'
        mock_settings.return_value.GCS_S3_REGION = 'us-east-1'

        # act
        service = StorageService()

        # assert
        assert service._client_params['endpoint_url'] == 'https://gcs'
        assert service._config.signature_version == 's3'

    @patch(
        'src.infra.repositories.storage_service.get_settings',
    )
    def test_init__pool_connections__is_20(
        self,
        mock_settings,
    ):
        """Test max_pool_connections is set to 20."""
        # arrange
        mock_settings.return_value.STORAGE_TYPE = 'local'
        mock_settings.return_value.BUCKET_PREFIX = 'test'
        mock_settings.return_value.SEAWEEDFS_S3_ENDPOINT = 'http://s3'
        mock_settings.return_value.SEAWEEDFS_S3_ACCESS_KEY = 'key'
        mock_settings.return_value.SEAWEEDFS_S3_SECRET_KEY = 'secret'
        mock_settings.return_value.SEAWEEDFS_S3_REGION = 'us-east-1'
        mock_settings.return_value.SEAWEEDFS_S3_USE_SSL = False

        # act
        service = StorageService()

        # assert
        assert service._config.max_pool_connections == 20


class TestStorageServiceUpload:
    """Tests for upload_file S3 error paths."""

    @pytest.fixture()
    def _service(self):
        """Create a StorageService with mock S3 client."""
        with patch(
            'src.infra.repositories.storage_service.get_settings',
        ) as mock_settings:
            mock_settings.return_value.STORAGE_TYPE = 'local'
            mock_settings.return_value.BUCKET_PREFIX = 'test'
            mock_settings.return_value.SEAWEEDFS_S3_ENDPOINT = 'http://s3'
            mock_settings.return_value.SEAWEEDFS_S3_ACCESS_KEY = 'key'
            mock_settings.return_value.SEAWEEDFS_S3_SECRET_KEY = 'secret'
            mock_settings.return_value.SEAWEEDFS_S3_REGION = 'us-east-1'
            mock_settings.return_value.SEAWEEDFS_S3_USE_SSL = False
            svc = StorageService()

        mock_client = AsyncMock()
        svc._s3_client = mock_client
        return svc, mock_client

    def _make_client_error(self, code: str) -> ClientError:
        """Create a botocore ClientError."""
        return ClientError(
            error_response={
                'Error': {'Code': code, 'Message': 'test'},
            },
            operation_name='TestOp',
        )

    async def test_upload__ok__no_error(self, _service):
        """Upload OK raises no error."""
        # arrange
        svc, mock_s3 = _service
        mock_s3.upload_fileobj = AsyncMock()
        stream = AsyncMock()

        # act — no exception
        await svc.upload_file('bucket', 'key', stream, 'image/png')

        # assert
        mock_s3.upload_fileobj.assert_called_once()

    async def test_upload__with_content_type__extra_args(
        self,
        _service,
    ):
        """Upload with content_type sets ExtraArgs."""
        # arrange
        svc, mock_s3 = _service
        mock_s3.upload_fileobj = AsyncMock()
        stream = AsyncMock()

        # act
        await svc.upload_file('b', 'k', stream, 'application/pdf')

        # assert
        call_kwargs = mock_s3.upload_fileobj.call_args
        assert call_kwargs.kwargs['ExtraArgs'] == {
            'ContentType': 'application/pdf',
        }

    async def test_upload__no_content_type__empty_extra(
        self,
        _service,
    ):
        """Upload without content_type has empty ExtraArgs."""
        # arrange
        svc, mock_s3 = _service
        mock_s3.upload_fileobj = AsyncMock()
        stream = AsyncMock()

        # act
        await svc.upload_file('b', 'k', stream, None)

        # assert
        call_kwargs = mock_s3.upload_fileobj.call_args
        assert call_kwargs.kwargs['ExtraArgs'] == {}

    async def test_upload__no_bucket__create_and_retry(
        self,
        _service,
    ):
        """NoSuchBucket → create bucket → retry upload."""
        # arrange
        svc, mock_s3 = _service
        error = self._make_client_error('NoSuchBucket')
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

    async def test_upload__bucket_create_fail__raise_err(
        self,
        _service,
    ):
        """NoSuchBucket → create fails → StorageError."""
        # arrange
        svc, mock_s3 = _service
        no_bucket = self._make_client_error('NoSuchBucket')
        create_err = self._make_client_error('AccessDenied')
        mock_s3.upload_fileobj = AsyncMock(
            side_effect=no_bucket,
        )
        mock_s3.create_bucket = AsyncMock(
            side_effect=create_err,
        )
        stream = AsyncMock()

        # act & assert
        with pytest.raises(StorageError) as exc_info:
            await svc.upload_file('bucket', 'key', stream, None)

        assert exc_info.value.error_code.code == 'STORAGE_004'

    async def test_upload__access_denied__raise_upload(
        self,
        _service,
    ):
        """Non-NoSuchBucket error → upload_failed."""
        # arrange
        svc, mock_s3 = _service
        error = self._make_client_error('AccessDenied')
        mock_s3.upload_fileobj = AsyncMock(side_effect=error)
        stream = AsyncMock()

        # act & assert
        with pytest.raises(StorageError) as exc_info:
            await svc.upload_file('bucket', 'key', stream, None)

        assert exc_info.value.error_code.code == 'STORAGE_002'


class TestStorageServiceDownload:
    """Tests for download_file S3 error paths."""

    @pytest.fixture()
    def _service(self):
        """Create a StorageService with mock S3 client."""
        with patch(
            'src.infra.repositories.storage_service.get_settings',
        ) as mock_settings:
            mock_settings.return_value.STORAGE_TYPE = 'local'
            mock_settings.return_value.BUCKET_PREFIX = 'test'
            mock_settings.return_value.SEAWEEDFS_S3_ENDPOINT = 'http://s3'
            mock_settings.return_value.SEAWEEDFS_S3_ACCESS_KEY = 'key'
            mock_settings.return_value.SEAWEEDFS_S3_SECRET_KEY = 'secret'
            mock_settings.return_value.SEAWEEDFS_S3_REGION = 'us-east-1'
            mock_settings.return_value.SEAWEEDFS_S3_USE_SSL = False
            mock_settings.return_value.CHUNK_SIZE = 1024
            svc = StorageService()

        mock_client = AsyncMock()
        svc._s3_client = mock_client
        return svc, mock_client

    def _make_client_error(self, code: str) -> ClientError:
        """Create a botocore ClientError."""
        return ClientError(
            error_response={
                'Error': {'Code': code, 'Message': 'test'},
            },
            operation_name='TestOp',
        )

    async def test_download__no_such_key__file_not_found(
        self,
        _service,
    ):
        """NoSuchKey → file_not_found_in_storage."""
        # arrange
        svc, mock_s3 = _service
        error = self._make_client_error('NoSuchKey')
        mock_s3.get_object = AsyncMock(side_effect=error)

        # act & assert
        with pytest.raises(StorageError) as exc_info:
            async for _ in svc.download_file('bucket', 'path'):
                pass

        assert exc_info.value.error_code.code == 'STORAGE_005'

    async def test_download__internal_err__raise_download(
        self,
        _service,
    ):
        """Non-NoSuchKey error → download_failed."""
        # arrange
        svc, mock_s3 = _service
        error = self._make_client_error('InternalError')
        mock_s3.get_object = AsyncMock(side_effect=error)

        # act & assert
        with pytest.raises(StorageError) as exc_info:
            async for _ in svc.download_file('bucket', 'path'):
                pass

        assert exc_info.value.error_code.code == 'STORAGE_003'

    async def test_download__with_range__range_in_kwargs(
        self,
        _service,
    ):
        """Range header passed to get_object kwargs."""
        # arrange
        svc, mock_s3 = _service

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


class TestStorageServiceDelete:
    """Tests for delete_file S3 error paths."""

    @pytest.fixture()
    def _service(self):
        """Create a StorageService with mock S3 client."""
        with patch(
            'src.infra.repositories.storage_service.get_settings',
        ) as mock_settings:
            mock_settings.return_value.STORAGE_TYPE = 'local'
            mock_settings.return_value.BUCKET_PREFIX = 'test'
            mock_settings.return_value.SEAWEEDFS_S3_ENDPOINT = 'http://s3'
            mock_settings.return_value.SEAWEEDFS_S3_ACCESS_KEY = 'key'
            mock_settings.return_value.SEAWEEDFS_S3_SECRET_KEY = 'secret'
            mock_settings.return_value.SEAWEEDFS_S3_REGION = 'us-east-1'
            mock_settings.return_value.SEAWEEDFS_S3_USE_SSL = False
            svc = StorageService()

        mock_client = AsyncMock()
        svc._s3_client = mock_client
        return svc, mock_client

    def _make_client_error(self, code: str) -> ClientError:
        """Create a botocore ClientError."""
        return ClientError(
            error_response={
                'Error': {'Code': code, 'Message': 'test'},
            },
            operation_name='TestOp',
        )

    async def test_delete__ok__no_error(self, _service):
        """Delete OK raises no error."""
        # arrange
        svc, mock_s3 = _service
        mock_s3.delete_object = AsyncMock()

        # act — no exception
        await svc.delete_file('bucket', 'key')

        # assert
        mock_s3.delete_object.assert_called_once_with(
            Bucket='bucket',
            Key='key',
        )

    async def test_delete__client_error__raise_storage(
        self,
        _service,
    ):
        """ClientError on delete → StorageError.delete_failed."""
        # arrange
        svc, mock_s3 = _service
        error = self._make_client_error('InternalError')
        mock_s3.delete_object = AsyncMock(side_effect=error)

        # act & assert
        with pytest.raises(StorageError) as exc_info:
            await svc.delete_file('bucket', 'key')

        assert exc_info.value.error_code.code == 'STORAGE_006'
