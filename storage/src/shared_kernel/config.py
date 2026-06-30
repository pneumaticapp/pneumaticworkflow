"""Application configuration settings."""

import json
import os
from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseAppSettings(BaseSettings):
    """Base application settings.

    Contains all shared configuration values.
    Environment-specific behavior is controlled by subclasses
    that override boolean flags, not by if-checks on CONFIG string.
    """

    model_config = SettingsConfigDict(
        env_file=('.env',),
        extra='ignore',
    )

    # ── Application ──────────────────────────────────────────
    PORT: int = 8000
    FRONTEND_URL: str | None = None
    FORMS_URL: str | None = None
    ALLOWED_ORIGINS: list[str] = ['http://localhost:3000']

    # ── Environment-specific flags ───────────────────────────
    # Subclasses override these instead of checking CONFIG string.
    DEBUG: bool = False
    HSTS_ENABLED: bool = False
    RATE_LIMIT_ENABLED: bool = True
    RELOAD: bool = False
    WORKERS: int = 1

    # ── Validators ───────────────────────────────────────────

    @field_validator('FASTAPI_BASE_URL', 'BACKEND_PRIVATE_URL', mode='after')
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        """Strip trailing slash from URLs."""
        return v.rstrip('/')

    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str) and not v.startswith('['):
            return [i.strip() for i in v.split(',')]
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            return json.loads(v)
        raise ValueError(v)

    @model_validator(mode='after')
    def append_frontend_urls(self) -> 'BaseAppSettings':
        """Add frontend/forms URLs to CORS origins."""
        if self.FRONTEND_URL and self.FRONTEND_URL not in self.ALLOWED_ORIGINS:
            self.ALLOWED_ORIGINS.append(self.FRONTEND_URL)
        if self.FORMS_URL and self.FORMS_URL not in self.ALLOWED_ORIGINS:
            self.ALLOWED_ORIGINS.append(self.FORMS_URL)
        return self

    # ── Database ─────────────────────────────────────────────
    POSTGRES_USER: str = 'pneumatic'
    POSTGRES_PASSWORD: str = 'pneumatic'  # noqa: S105
    POSTGRES_DB: str = 'pneumatic'
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: int = 5432

    # ── Storage ──────────────────────────────────────────────
    STORAGE_TYPE: Literal['local', 'google'] = 'local'

    # Google Cloud Storage S3 API settings
    GCS_S3_ENDPOINT: str = 'https://storage.googleapis.com'
    GCS_S3_ACCESS_KEY: str = ''  # HMAC access key
    GCS_S3_SECRET_KEY: str = ''  # HMAC secret key
    GCS_S3_REGION: str = 'us-east-1'  # GCS requires specific region

    # SeaweedFS S3 (when STORAGE_TYPE='local')
    SEAWEEDFS_S3_ENDPOINT: str = 'http://seaweedfs-filer:8333'
    SEAWEEDFS_S3_ACCESS_KEY: str = 'any-access-key-will-work'
    SEAWEEDFS_S3_SECRET_KEY: str = 'any-secret-key-will-work'  # noqa: S105
    SEAWEEDFS_S3_REGION: str = 'us-east-1'
    SEAWEEDFS_S3_USE_SSL: bool = False

    # ── Rate limits ──────────────────────────────────────────
    RATE_LIMIT_UPLOAD_REQUESTS: int = 10
    RATE_LIMIT_UPLOAD_WINDOW: int = 60
    RATE_LIMIT_DOWNLOAD_REQUESTS: int = 100
    RATE_LIMIT_DOWNLOAD_WINDOW: int = 60

    # ── File service ─────────────────────────────────────────
    FASTAPI_BASE_URL: str = 'http://localhost:8002'
    BUCKET_PREFIX: str = 'pneumatic-dev-test'
    MAX_FILE_SIZE: int = 104857600
    CHUNK_SIZE: int = 1048576  # 1MB chunks for file streaming

    # ── Redis ────────────────────────────────────────────────
    AUTH_REDIS_URL: str = 'redis://:redis_password@redis:6379/1'
    KEY_PREFIX_REDIS: str = ':1:'

    # ── Auth ─────────────────────────────────────────────────
    DJANGO_SECRET_KEY: str  # Required, no default (security)
    # AUTH_TOKEN_ITERATIONS = 1 is a trade-off.
    # Must match Django backend. Security relies
    # on Redis access control.
    AUTH_TOKEN_ITERATIONS: int = 1

    # ── Django backend ───────────────────────────────────────
    BACKEND_PRIVATE_URL: str = 'http://localhost:8001'

    # ── Computed properties ──────────────────────────────────

    @property
    def root_path(self) -> str:
        """Derive ASGI root_path from FASTAPI_BASE_URL."""
        path = urlparse(self.FASTAPI_BASE_URL).path
        return path.rstrip('/') or ''

    @property
    def check_permission_url(self) -> str:
        """Generate permission check URL."""
        return f'{self.BACKEND_PRIVATE_URL}/attachments/check-permission'

    @property
    def database_url(self) -> str:
        """Generate database URL."""
        return (
            f'postgresql+asyncpg://'
            f'{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@'
            f'{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
        )


class TestingSettings(BaseAppSettings):
    """Testing environment settings."""

    DEBUG: bool = True
    HSTS_ENABLED: bool = False
    RATE_LIMIT_ENABLED: bool = False
    RELOAD: bool = False
    WORKERS: int = 1


class DevelopmentSettings(BaseAppSettings):
    """Development environment settings."""

    DEBUG: bool = True
    HSTS_ENABLED: bool = False
    RATE_LIMIT_ENABLED: bool = False
    RELOAD: bool = True
    WORKERS: int = 1


class ProductionSettings(BaseAppSettings):
    """Production environment settings.

    Enables HSTS and rate limiting,
    disables hot reload.
    """

    DEBUG: bool = False
    HSTS_ENABLED: bool = True
    RATE_LIMIT_ENABLED: bool = True
    RELOAD: bool = False
    # WORKERS read from env (default 1, but Production
    # deployments typically set WORKERS=4+ via env var)


# ── Settings Factory ─────────────────────────────────────────

_CONFIG_MAP: dict[str, type[BaseAppSettings]] = {
    'Testing': TestingSettings,
    'Development': DevelopmentSettings,
    'Production': ProductionSettings,
}


@lru_cache
def get_settings() -> BaseAppSettings:
    """Get application settings based on CONFIG env var.

    Uses CONFIG environment variable to select the settings class.
    Defaults to DevelopmentSettings if CONFIG is not set.

    Returns:
        Environment-specific settings instance.

    """
    config_name = os.getenv('CONFIG', 'Development')
    settings_class = _CONFIG_MAP.get(config_name, DevelopmentSettings)
    return settings_class()
