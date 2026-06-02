"""Fixtures specific to unit tests."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from botocore.exceptions import ClientError
from fastapi import Request
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from starlette.testclient import TestClient

from src.infra.adapters.storage_service import (
    StorageService,
    StorageServiceHolder,
)
from src.infra.http_client import HttpClient, SharedClientHolder
from src.infra.repositories.file_record_repository import (
    FileRecordRepository,
)
from src.shared_kernel.auth.redis_client import (
    RedisAuthClient,
    get_redis_client,
)
from src.shared_kernel.auth.token_auth import _compute_pbkdf2
from src.shared_kernel.auth.user_types import UserType
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
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
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


# --- rate_limit config ---


@pytest.fixture
def fast_rate_limits():
    """Low limits for fast rate limit testing."""
    return {
        'upload': _RateLimit(
            max_requests=2,
            window_seconds=60,
        ),
        'download': _RateLimit(
            max_requests=3,
            window_seconds=60,
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


# --- permissions fixtures ---


@pytest.fixture
def make_perm_request():
    """Factory for mock requests with optional user."""

    def _factory(user=None, *, has_user: bool = True):
        request = MagicMock(spec=Request)
        if has_user and user is not None:
            request.state.user = user
        elif not has_user:
            del request.state.user
            request.state = MagicMock(spec=[])
        else:
            request.state.user = None
        return request

    return _factory


@pytest.fixture
def make_perm_user():
    """Factory for mock users."""

    def _factory(
        auth_type: str = UserType.AUTHENTICATED,
        is_anonymous: bool = False,
    ):
        user = MagicMock()
        user.auth_type = auth_type
        user.is_anonymous = is_anonymous
        return user

    return _factory


# --- rate_limit request factory ---


@pytest.fixture
def make_rate_request():
    """Factory for mock rate-limit requests."""

    def _factory(
        path='/upload',
        method='POST',
        client_ip='127.0.0.1',
    ):
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = path
        request.method = method
        request.headers = {}
        request.client = MagicMock()
        request.client.host = client_ip
        return request

    return _factory


# --- redis cache management ---


@pytest.fixture(autouse=False)
def clear_redis_cache():
    """Clear lru_cache before and after test."""
    get_redis_client.cache_clear()
    yield
    get_redis_client.cache_clear()


# --- client error factory ---


@pytest.fixture
def make_client_error():
    """Factory for botocore ClientError."""

    def _factory(code: str) -> ClientError:
        return ClientError(
            error_response={
                'Error': {
                    'Code': code,
                    'Message': 'test',
                },
            },
            operation_name='TestOp',
        )

    return _factory


# --- mock fixtures ---


@pytest.fixture
def mock_redis_settings(mocker):
    """Mock for get_settings in redis_client module."""
    return mocker.patch(
        'src.shared_kernel.auth.redis_client.get_settings',
    )


@pytest.fixture
def mock_get_settings(mocker):
    """Mock for get_settings."""
    return mocker.patch(
        'src.shared_kernel.auth.token_auth.get_settings',
    )


@pytest.fixture
def mock_get_redis_client(mocker):
    """Mock for get_redis_client."""
    return mocker.patch(
        'src.shared_kernel.auth.token_auth.get_redis_client',
    )


@pytest.fixture
def mock_httpx_post(mocker):
    """Mock for httpx.AsyncClient.post."""
    return mocker.patch('httpx.AsyncClient.post')


@pytest.fixture
def mock_redis_from_url(mocker):
    """Mock for redis.asyncio.from_url."""
    return mocker.patch('redis.asyncio.from_url')


@pytest.fixture
def mock_redis_auth_client_get(mocker):
    """Mock for RedisAuthClient.get."""
    return mocker.patch(
        'src.shared_kernel.auth.redis_client.RedisAuthClient.get',
    )


@pytest.fixture
def mock_get_db_session(mocker):
    """Mock for get_db_session."""
    return mocker.patch(
        'src.shared_kernel.di.container.get_db_session',
    )


@pytest.fixture
def mock_upload_use_case_execute(mocker):
    """Mock for UploadFileUseCase.execute."""
    return mocker.patch(
        'src.application.use_cases.file_upload.UploadFileUseCase.execute',
    )


@pytest.fixture
def mock_download_use_case_get_metadata(mocker):
    """Mock for DownloadFileUseCase.get_metadata."""
    return mocker.patch(
        'src.application.use_cases.file_download.'
        'DownloadFileUseCase.get_metadata',
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_download_use_case_get_stream(mocker):
    """Mock for DownloadFileUseCase.get_stream."""
    return mocker.patch(
        'src.application.use_cases.file_download.'
        'DownloadFileUseCase.get_stream',
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_pneumatic_token_data(mocker):
    """Mock for PneumaticToken.data."""
    return mocker.patch(
        'src.shared_kernel.auth.token_auth.PneumaticToken.data',
    )


@pytest.fixture
def mock_http_client_check_permission(mocker):
    """Mock for HttpClient.check_file_permission."""
    return mocker.patch(
        'src.infra.http_client.HttpClient.check_file_permission',
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_aioboto3_session(mocker):
    """Mock for aioboto3.Session."""
    return mocker.patch('aioboto3.Session')


@pytest.fixture
def mock_auth_middleware_authenticate_token(mocker):
    """Mock for AuthenticationMiddleware.authenticate_token."""
    return mocker.patch(
        'src.shared_kernel.middleware.auth_middleware'
        '.AuthenticationMiddleware.authenticate_token',
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_auth_middleware_pneumatic_token_data(mocker):
    """Mock for PneumaticToken.data in auth middleware."""
    return mocker.patch(
        'src.shared_kernel.middleware.auth_middleware.PneumaticToken.data',
    )
