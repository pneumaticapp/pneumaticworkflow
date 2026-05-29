"""Fixtures specific to unit tests."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Request
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from starlette.testclient import TestClient

from src.infra.http_client import HttpClient, SharedClientHolder
from src.infra.repositories.file_record_repository import (
    FileRecordRepository,
)
from src.infra.repositories.storage_service import (
    StorageService,
    StorageServiceHolder,
)
from src.shared_kernel.auth.redis_client import RedisAuthClient
from src.shared_kernel.auth.token_auth import _compute_pbkdf2
from src.shared_kernel.database.models import FileRecordORM
from src.shared_kernel.middleware.auth_middleware import (
    AuthenticationMiddleware,
)
from src.shared_kernel.middleware.rate_limit import _RateLimit
from src.shared_kernel.middleware.security_headers import (
    SecurityHeadersMiddleware,
)

# --- auth_middleware fixtures ---


@pytest.fixture
def auth_mw_app():
    """Mock FastAPI app for AuthenticationMiddleware."""
    return Mock()


@pytest.fixture
def auth_middleware(auth_mw_app):
    """AuthenticationMiddleware instance with require_auth=True."""
    return AuthenticationMiddleware(auth_mw_app, require_auth=True)


@pytest.fixture
def auth_middleware_no_auth(auth_mw_app):
    """AuthenticationMiddleware without required auth."""
    return AuthenticationMiddleware(auth_mw_app, require_auth=False)


@pytest.fixture
def auth_mw_request():
    """Mock request for auth middleware tests."""
    request = Mock(spec=Request)
    request.state = type('State', (), {})()
    request.cookies = {}
    return request


@pytest.fixture
def auth_mw_call_next():
    """Mock call_next function for middleware dispatch."""

    async def _call_next(request):
        return Response(content='OK', status_code=200)

    return _call_next


# --- file_record_repository fixtures ---


@pytest.fixture
def repo_mock_session():
    """Mock database session for repository tests."""
    return AsyncMock()


@pytest.fixture
def file_record_repository(repo_mock_session):
    """FileRecordRepository instance with mocked session."""
    return FileRecordRepository(repo_mock_session)


@pytest.fixture
def sample_file_record_orm():
    """Sample FileRecordORM for repository tests."""
    return FileRecordORM(
        file_id='12345678-1234-5678-1234-567812345678',
        filename='test.txt',
        content_type='text/plain',
        size=1024,
        user_id=1,
        account_id=1,
        created_at=datetime.now(UTC),
    )


# --- http_client fixtures ---


@pytest.fixture
def http_client():
    """HttpClient instance for tests."""
    return HttpClient(base_url='http://test.example.com')


# --- security_headers fixtures ---


def _sec_homepage(request):
    """Simple test endpoint for security headers."""
    return PlainTextResponse('ok')


@pytest.fixture
def sec_headers_client():
    """Test client without HSTS."""
    app = Starlette(routes=[Route('/', _sec_homepage)])
    app.add_middleware(SecurityHeadersMiddleware, include_hsts=False)
    return TestClient(app)


@pytest.fixture
def sec_headers_client_hsts():
    """Test client with HSTS enabled."""
    app = Starlette(routes=[Route('/', _sec_homepage)])
    app.add_middleware(SecurityHeadersMiddleware, include_hsts=True)
    return TestClient(app)


# --- rate_limit fixtures ---


@pytest.fixture
def fast_rate_limits():
    """Low limits for fast rate limit testing."""
    return {
        'upload': _RateLimit(
            max_requests=2, window_seconds=60,
        ),
        'download': _RateLimit(
            max_requests=3, window_seconds=60,
        ),
    }


# --- redis_client fixtures ---


@pytest.fixture
def unit_mock_redis_client():
    """Mock Redis client for unit tests."""
    return AsyncMock()


@pytest.fixture
def redis_auth_client(unit_mock_redis_client, mock_redis_from_url):
    """RedisAuthClient instance with mocked Redis."""
    mock_redis_from_url.return_value = unit_mock_redis_client
    return RedisAuthClient('redis://localhost:6379')


# --- token_auth fixtures ---


@pytest.fixture
def clear_pbkdf2_cache():
    """Clear LRU cache before and after test."""
    _compute_pbkdf2.cache_clear()
    yield
    _compute_pbkdf2.cache_clear()


# --- storage_holder fixtures ---


@pytest.fixture
def reset_storage_holder():
    """Reset StorageServiceHolder state."""
    StorageServiceHolder._instance = None
    yield
    StorageServiceHolder._instance = None


@pytest.fixture
def reset_shared_client_holder():
    """Reset SharedClientHolder state."""
    SharedClientHolder._instance = None
    yield
    SharedClientHolder._instance = None


@pytest.fixture
def mock_storage_settings(mocker):
    """Mock get_settings for StorageService with standard params."""
    mock_settings = mocker.patch(
        'src.infra.repositories.storage_service.get_settings',
    )
    mock_settings.return_value.STORAGE_TYPE = 'local'
    mock_settings.return_value.BUCKET_PREFIX = 'test'
    mock_settings.return_value.SEAWEEDFS_S3_ENDPOINT = 'http://s3'
    mock_settings.return_value.SEAWEEDFS_S3_ACCESS_KEY = 'key'
    mock_settings.return_value.SEAWEEDFS_S3_SECRET_KEY = 'secret'
    mock_settings.return_value.SEAWEEDFS_S3_REGION = 'us-east-1'
    mock_settings.return_value.SEAWEEDFS_S3_USE_SSL = False
    return mock_settings


@pytest.fixture
def storage_service_with_mock_s3(mock_storage_settings):
    """StorageService with mock S3 client pre-injected."""
    svc = StorageService()
    mock_client = AsyncMock()
    svc._s3_client = mock_client
    return svc, mock_client
