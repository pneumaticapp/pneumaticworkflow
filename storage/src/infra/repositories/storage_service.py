"""Storage service for file operations."""

from collections.abc import AsyncGenerator

import aioboto3
from aiobotocore.config import AioConfig
from botocore.exceptions import ClientError

from src.shared_kernel.config import get_settings
from src.shared_kernel.exceptions import (
    MSG_STORAGE_009,
    MSG_STORAGE_010,
    MSG_STORAGE_011,
    StorageError,
)


class StorageService:
    """Storage service supporting both S3 and Google Cloud Storage."""

    def __init__(self) -> None:
        """Initialize storage service."""
        self._settings = get_settings()
        self._bucket_prefix = self._settings.BUCKET_PREFIX
        self._storage_type = self._settings.STORAGE_TYPE
        self._session: aioboto3.Session | None = None

        # Configuration for increasing connection pool
        # GCS requires signature_version='s3' (legacy), not 's3v4'!
        signature_version = 's3' if self._storage_type == 'google' else 's3v4'
        self._config = AioConfig(
            max_pool_connections=10,
            retries={'max_attempts': 3, 'mode': 'standard'},
            signature_version=signature_version,
        )

        # Connection parameters depending on storage type
        if self._storage_type == 'local':
            # Parameters for SeaweedFS S3
            self._client_params = {
                'service_name': 's3',
                'endpoint_url': self._settings.SEAWEEDFS_S3_ENDPOINT,
                'aws_access_key_id': self._settings.SEAWEEDFS_S3_ACCESS_KEY,
                'region_name': self._settings.SEAWEEDFS_S3_REGION,
                'use_ssl': self._settings.SEAWEEDFS_S3_USE_SSL,
                'config': self._config,
                'aws_secret_access_key': (
                    self._settings.SEAWEEDFS_S3_SECRET_KEY
                ),
            }
        else:
            # Parameters for Google Cloud Storage via S3 API
            self._client_params = {
                'service_name': 's3',
                'endpoint_url': self._settings.GCS_S3_ENDPOINT,
                'aws_access_key_id': self._settings.GCS_S3_ACCESS_KEY,
                'aws_secret_access_key': self._settings.GCS_S3_SECRET_KEY,
                'region_name': self._settings.GCS_S3_REGION,
                'config': self._config,
            }

    def _get_session(self) -> aioboto3.Session:
        """Get or create aioboto3 session."""
        if self._session is None:
            self._session = aioboto3.Session()
        return self._session

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
        file_content: bytes,
        content_type: str | None,
    ) -> None:
        """Upload file to storage.

        Args:
            bucket_name: Bucket name.
            file_path: File path in bucket.
            file_content: File content.
            content_type: File MIME type.

        Returns:
            None.

        """
        session = self._get_session()

        async with session.client(**self._client_params) as s3:
            try:
                # Try to create bucket if it doesn't exist
                try:
                    # For GCS don't specify LocationConstraint when creating
                    await s3.create_bucket(Bucket=bucket_name)
                except ClientError as e:
                    if e.response['Error']['Code'] not in (
                        'BucketAlreadyExists',
                        'BucketAlreadyOwnedByYou',
                    ):
                        raise StorageError(
                            MSG_STORAGE_009.format(details=str(e)),
                        ) from e

                # Upload file
                await s3.put_object(
                    Bucket=bucket_name,
                    Key=file_path,
                    Body=file_content,
                    ContentType=content_type,
                )
            except ClientError as e:
                raise StorageError(
                    MSG_STORAGE_010.format(details=str(e))
                ) from e

    async def download_file(
        self,
        bucket_name: str,
        file_path: str,
    ) -> AsyncGenerator[bytes, None]:
        """Download file as stream.

        Args:
            bucket_name: Bucket name.
            file_path: File path in storage.

        Yields:
            bytes: File chunks.

        Raises:
            StorageError: On download error.

        """
        chunk_size = self._settings.CHUNK_SIZE
        session = self._get_session()

        async with session.client(**self._client_params) as s3:
            try:
                # Get object
                response = await s3.get_object(
                    Bucket=bucket_name,
                    Key=file_path,
                )

                body = response['Body']
                async for chunk in body.iter_chunks(chunk_size=chunk_size):
                    yield chunk

            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'NoSuchKey':
                    error_msg = (
                        f'File {file_path} not found in bucket {bucket_name}'
                    )
                    raise StorageError(error_msg) from e
                raise StorageError(
                    MSG_STORAGE_011.format(details=str(e))
                ) from e
