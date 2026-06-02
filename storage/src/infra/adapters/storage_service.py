"""Storage service for file operations."""

import asyncio
import typing
from collections.abc import AsyncGenerator

import aioboto3
from aiobotocore.config import AioConfig
from botocore.exceptions import ClientError

from src.shared_kernel.config import get_settings
from src.shared_kernel.exceptions import StorageError


class StorageService:
    """Storage service supporting both S3 and Google Cloud Storage.

    Uses a persistent S3 client for connection reuse across
    requests instead of creating a new client per operation.
    """

    def __init__(self) -> None:
        """Initialize storage service."""
        self._settings = get_settings()
        self._bucket_prefix = self._settings.BUCKET_PREFIX
        self._storage_type = self._settings.STORAGE_TYPE
        self._session = aioboto3.Session()

        # GCS requires signature_version='s3' (legacy), not 's3v4'!
        signature_version = 's3' if self._storage_type == 'google' else 's3v4'
        self._config = AioConfig(
            max_pool_connections=20,
            retries={'max_attempts': 3, 'mode': 'standard'},
            signature_version=signature_version,
        )

        # Connection parameters depending on storage type
        if self._storage_type == 'local':
            self._client_params = {
                'service_name': 's3',
                'endpoint_url': (self._settings.SEAWEEDFS_S3_ENDPOINT),
                'aws_access_key_id': (self._settings.SEAWEEDFS_S3_ACCESS_KEY),
                'region_name': self._settings.SEAWEEDFS_S3_REGION,
                'use_ssl': self._settings.SEAWEEDFS_S3_USE_SSL,
                'config': self._config,
                'aws_secret_access_key': (
                    self._settings.SEAWEEDFS_S3_SECRET_KEY
                ),
            }
        else:
            self._client_params = {
                'service_name': 's3',
                'endpoint_url': self._settings.GCS_S3_ENDPOINT,
                'aws_access_key_id': (self._settings.GCS_S3_ACCESS_KEY),
                'aws_secret_access_key': (self._settings.GCS_S3_SECRET_KEY),
                'region_name': self._settings.GCS_S3_REGION,
                'config': self._config,
            }

        # Persistent S3 client (lazy-initialized)
        self._s3_client: typing.Any | None = None
        self._s3_context: typing.Any | None = None

    async def _get_client(self) -> typing.Any:  # noqa: ANN401
        """Get or create persistent S3 client.

        Returns:
            S3 client instance.

        """
        if self._s3_client is None:
            self._s3_context = self._session.client(
                **self._client_params,
            )
            self._s3_client = await self._s3_context.__aenter__()
        return self._s3_client

    async def close(self) -> None:
        """Close persistent S3 client."""
        if self._s3_context is not None:
            await self._s3_context.__aexit__(None, None, None)
            self._s3_client = None
            self._s3_context = None

    def get_storage_path(
        self,
        account_id: int,
        file_id: str,
    ) -> tuple[str, str]:
        """Generate storage path.

        Args:
            account_id: Account ID.
            file_id: File ID.

        Returns:
            tuple: (bucket_name, file_path).

        """
        bucket_name = f'{self._bucket_prefix}-{account_id}'
        file_path = file_id
        return bucket_name, file_path

    async def upload_file(
        self,
        bucket_name: str,
        file_path: str,
        file_stream: typing.IO[bytes],
        content_type: str | None,
    ) -> None:
        """Upload file to storage.

        Args:
            bucket_name: Bucket name.
            file_path: File path in bucket.
            file_stream: File stream.
            content_type: File MIME type.

        Returns:
            None.

        """
        s3 = await self._get_client()

        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type

        try:
            await s3.upload_fileobj(
                Fileobj=file_stream,
                Bucket=bucket_name,
                Key=file_path,
                ExtraArgs=extra_args,
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                try:
                    await s3.create_bucket(Bucket=bucket_name)
                except ClientError as create_e:
                    raise StorageError.bucket_create_failed(
                        details=str(create_e),
                    ) from create_e

                try:
                    file_stream.seek(0)
                    await s3.upload_fileobj(
                        Fileobj=file_stream,
                        Bucket=bucket_name,
                        Key=file_path,
                        ExtraArgs=extra_args,
                    )
                    return  # noqa: TRY300
                except ClientError as upload_e:
                    raise StorageError.upload_failed(
                        details=str(upload_e),
                    ) from upload_e

            raise StorageError.upload_failed(
                details=str(e),
            ) from e

    async def download_file(
        self,
        bucket_name: str,
        file_path: str,
        range_header: str | None = None,
    ) -> AsyncGenerator[bytes, None]:
        """Download file as stream.

        Args:
            bucket_name: Bucket name.
            file_path: File path in storage.
            range_header: Optional HTTP Range header.

        Yields:
            bytes: File chunks.

        Raises:
            StorageError: On download error.

        """
        chunk_size = self._settings.CHUNK_SIZE
        s3 = await self._get_client()

        try:
            kwargs = {
                'Bucket': bucket_name,
                'Key': file_path,
            }
            if range_header:
                kwargs['Range'] = range_header

            response = await s3.get_object(**kwargs)

            body = response['Body']
            async for chunk in body.iter_chunks(
                chunk_size=chunk_size,
            ):
                yield chunk

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise StorageError.file_not_found_in_storage(
                    file_path=file_path,
                    bucket_name=bucket_name,
                ) from e
            raise StorageError.download_failed(
                details=str(e),
            ) from e

    async def delete_file(
        self,
        bucket_name: str,
        file_path: str,
    ) -> None:
        """Delete file from storage.

        Args:
            bucket_name: Bucket name.
            file_path: File path in storage.

        Raises:
            StorageError: On deletion error.

        """
        s3 = await self._get_client()

        try:
            await s3.delete_object(
                Bucket=bucket_name,
                Key=file_path,
            )
        except ClientError as e:
            raise StorageError.delete_failed(
                details=str(e),
            ) from e


class StorageServiceHolder:
    """Singleton holder for StorageService.

    Follows the SharedClientHolder pattern used by HttpClient.
    Uses asyncio.Lock to prevent race condition on first init.
    """

    _instance: StorageService | None = None
    _lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    async def get(cls) -> StorageService:
        """Get or create StorageService singleton."""
        if cls._instance is None:
            async with cls._lock:
                # Double-checked locking
                if cls._instance is None:
                    cls._instance = StorageService()
        return cls._instance

    @classmethod
    async def close(cls) -> None:
        """Close StorageService and release S3 connections."""
        if cls._instance is not None:
            await cls._instance.close()
            cls._instance = None
