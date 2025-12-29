"""Application configuration settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    DEBUG: bool = True
    CONFIG: str = 'Development'
    WORKERS: int = 1
    PORT: int = 8002
    ALLOWED_ORIGINS: list[str] = ['*']

    # Database
    POSTGRES_USER: str = 'pneumatic'
    POSTGRES_PASSWORD: str = 'pneumatic'
    POSTGRES_DB: str = 'pneumatic'
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: int = 5433

    # Storage configuration
    STORAGE_TYPE: Literal['local', 'google'] = 'local'

    # Google Cloud Storage S3 API settings
    GCS_S3_ENDPOINT: str = 'https://storage.googleapis.com'
    GCS_S3_ACCESS_KEY: str = ''  # HMAC access key
    GCS_S3_SECRET_KEY: str = ''  # HMAC secret key
    GCS_S3_REGION: str = 'us-east-1'  # GCS requires specific region

    # SeaweedFS S3 (when STORAGE_TYPE='local')
    SEAWEEDFS_S3_ENDPOINT: str = 'http://seaweedfs-filer:8333'
    SEAWEEDFS_S3_ACCESS_KEY: str = 'any-access-key-will-work'
    SEAWEEDFS_S3_SECRET_KEY: str = 'any-secret-key-will-work'
    SEAWEEDFS_S3_REGION: str = 'us-east-1'
    SEAWEEDFS_S3_USE_SSL: bool = False

    # File service
    FASTAPI_BASE_URL: str = 'http://localhost:8000'
    BUCKET_PREFIX: str = 'pneumatic-dev-test'
    MAX_FILE_SIZE: int = 104857600
    CHUNK_SIZE: int = 1048576  # 1MB chunks for file streaming

    # Redis for authentication
    AUTH_REDIS_URL: str = 'redis://:redis_password@127.0.0.1:6379/1'
    KEY_PREFIX_REDIS: str = ':1:'

    # Django secret key for token decoding
    DJANGO_SECRET_KEY: str = 'DJANGO_SECRET_KEY'
    AUTH_TOKEN_ITERATIONS: int = 1

    # JWT settings
    JWT_SECRET_KEY: str = 'JWT_SECRET_KEY'
    JWT_ALGORITHM: str = 'HS256'

    # Django backend base URL
    DJANGO_BACKEND_URL: str = 'http://pneumatic-backend:8000'

    # Django backend URL for permission checks
    CHECK_PERMISSION_URL: str = (
        f'{DJANGO_BACKEND_URL}/attachments/check-permission'
    )

    @property
    def database_url(self) -> str:
        """Generate database URL."""
        return (
            f'postgresql+asyncpg://'
            f'{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@'
            f'{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
        )

    class Config:
        """Pydantic configuration."""

        env_file = ('.env',)
        extra = 'ignore'


@lru_cache
def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
