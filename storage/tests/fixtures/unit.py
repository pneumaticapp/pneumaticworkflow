"""Fixtures specific to unit tests."""

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from botocore.exceptions import ClientError
from fastapi import Request
from starlette.applications import Starlette
from starlette.datastructures import Headers
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
from src.shared_kernel.auth.user_types import ActorType, UserType
from src.shared_kernel.database.models import FileRecordORM
from src.shared_kernel.events.emitter import EventEmitter, get_event_emitter
from src.shared_kernel.events.request_events import RequestEvents
from src.shared_kernel.events.schema import (
    SERVICE_NAME,
    Actor,
    Event,
    EventName,
    RequestContext,
)
from src.shared_kernel.middleware.auth_middleware import (
    AuthenticationMiddleware,
)
from src.shared_kernel.middleware.rate_limit import _RateLimit
from src.shared_kernel.middleware.request_id import RequestIdMiddleware
from src.shared_kernel.middleware.security_headers import (
    SecurityHeadersMiddleware,
)

# The record the backend tests read back: one file for both writers.
# parents[3] is the repository root: fixtures -> tests -> storage -> root.
BACKEND_CONTRACT_DIR = (
    Path(__file__).resolve().parents[3]
    / 'backend'
    / 'src'
    / 'logs'
    / 'events'
    / 'tests'
    / 'fixtures'
)
BACKEND_CONTRACT_PATH = BACKEND_CONTRACT_DIR / 'file_service_record.json'
BACKEND_UPLOAD_CONTRACT_PATH = (
    BACKEND_CONTRACT_DIR / 'file_service_upload_record.json'
)
BACKEND_DENIED_CONTRACT_PATH = (
    BACKEND_CONTRACT_DIR / 'file_service_denied_record.json'
)
BACKEND_SERVICE_CONTRACT_PATH = (
    BACKEND_CONTRACT_DIR / 'file_service_contract.json'
)
CONTRACT_FILE_ID = '0f8fad5b-d9cb-469f-a165-70867728950e'
CONTRACT_TS = datetime(2026, 9, 9, 12, 0, 0, 123, tzinfo=UTC)
# The id the endpoint tests download and upload.
API_FILE_ID = '12345678-1234-5678-1234-567812345678'
# Host and password of the emitter under test: both are secrets the
# emitter must keep out of its log lines, the tests look for them there.
EMITTER_REDIS_HOST = 'redis-host.test'
EMITTER_REDIS_PASSWORD = 'emitter-secret'
EMITTER_REDIS_URL = (
    f'redis://:{EMITTER_REDIS_PASSWORD}@{EMITTER_REDIS_HOST}:6379/4'
)
EMITTER_STREAM_KEY = 'pneumatic:events'
EMITTER_MAXLEN = 10


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
    request = MagicMock(spec=Request)
    request.state = type('State', (), {})()
    request.cookies = {}
    request.url.path = '/'
    request.url.query = ''
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
        'src.infra.adapters.storage_service.get_settings',
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


# --- events fixtures ---


class CapturingEmitter:
    """Emitter of the unit tests: keeps the records instead of Redis."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    async def emit(self, event: Event) -> None:
        self.events.append(event)


def _read_contract(path: Path) -> dict:
    """Read a shared contract record, or say why it cannot be read."""
    if not path.is_file():
        msg = (
            f'The backend contract fixture is missing: {path}. '
            f'The file service and the backend share one record shape '
            f'and these files are it.'
        )
        raise AssertionError(msg)
    return json.loads(path.read_text(encoding='utf-8'))


@pytest.fixture
def backend_contract_record():
    """The record both writers agree on, read from the backend copy.

    Missing means the contract cannot be checked at all, which is the
    thing this fixture exists to prevent: it fails instead of skipping,
    so a checkout or an image that cannot see the file says so.
    """
    return _read_contract(BACKEND_CONTRACT_PATH)


@pytest.fixture
def backend_upload_contract_record():
    """The upload record both writers agree on."""
    return _read_contract(BACKEND_UPLOAD_CONTRACT_PATH)


@pytest.fixture
def backend_denied_contract_record():
    """The refusal record both writers agree on."""
    return _read_contract(BACKEND_DENIED_CONTRACT_PATH)


@pytest.fixture
def backend_service_contract():
    """The names both writers agree on: the stream and the actor types."""
    return _read_contract(BACKEND_SERVICE_CONTRACT_PATH)


@pytest.fixture
def sample_upload_event(sample_context):
    """Upload record of the contract."""
    return Event(
        type=EventName.FILE_UPLOAD,
        service=SERVICE_NAME,
        ts=CONTRACT_TS,
        account_id=42,
        actor=Actor(type=ActorType.USER, id=17),
        file_id=CONTRACT_FILE_ID,
        context=sample_context,
        payload={
            'filename': 'Contract Ann Smith.pdf',
            'size': 12345,
            'content_type': 'application/pdf',
        },
    )


@pytest.fixture
def sample_denied_event(sample_context):
    """Refusal record of the contract, for a file of another account."""
    return Event(
        type=EventName.FILE_ACCESS_DENIED,
        service=SERVICE_NAME,
        ts=CONTRACT_TS,
        account_id=42,
        actor=Actor(type=ActorType.USER, id=17),
        file_id=CONTRACT_FILE_ID,
        context=sample_context,
        payload={
            'filename': 'Contract Ann Smith.pdf',
            'size': 12345,
            'content_type': 'application/pdf',
            'file_account_id': 99,
        },
    )


@pytest.fixture
def sample_context():
    """HTTP context of the contract record."""
    return RequestContext(
        ip='203.0.113.7',
        user_agent='Mozilla/5.0 (X11; Linux x86_64)',
        request_id='3f9c2c1e6d0b4a0f9e2b7c1d5a6e8f90',
    )


@pytest.fixture
def sample_event(sample_context):
    """Download record of the contract."""
    return Event(
        type=EventName.FILE_DOWNLOAD,
        service=SERVICE_NAME,
        ts=CONTRACT_TS,
        account_id=42,
        actor=Actor(type=ActorType.USER, id=17),
        file_id=CONTRACT_FILE_ID,
        context=sample_context,
        payload={
            'filename': 'Contract Ann Smith.pdf',
            'size': 12345,
            'content_type': 'application/pdf',
            'is_owner': True,
        },
    )


@pytest.fixture
def capturing_emitter():
    """Emitter that keeps the records."""
    return CapturingEmitter()


@pytest.fixture
def events_emitter(mock_events_redis_from_url):
    """Enabled emitter of the unit tests; the Redis client is mocked.

    The mock is a dependency and not a convention: without it the
    first test that forgets to ask for it dials a real host.
    """
    return EventEmitter(
        url=EMITTER_REDIS_URL,
        key=EMITTER_STREAM_KEY,
        maxlen=EMITTER_MAXLEN,
        enabled=True,
    )


@pytest.fixture
def sample_stream_fields(sample_event):
    """The fields xadd writes for the sample event."""
    return {
        'type': 'file.download',
        'data': json.dumps(sample_event.to_dict()),
    }


@pytest.fixture
def clear_event_emitter_cache():
    """Clear the process emitter before and after the test."""
    get_event_emitter.cache_clear()
    yield
    get_event_emitter.cache_clear()


@pytest.fixture
def request_events(capturing_emitter, sample_context):
    """RequestEvents bound to the contract context."""
    return RequestEvents(
        emitter=capturing_emitter,
        context=sample_context,
    )


@pytest.fixture
def actor_user():
    """The actor of the contract record."""
    return Mock(user_id=17, account_id=42, actor_type=ActorType.USER)


@pytest.fixture
def mock_request_events_now(mocker):
    """Fixed moment for the records of RequestEvents."""
    return mocker.patch(
        'src.shared_kernel.events.request_events._now',
        return_value=CONTRACT_TS,
    )


@pytest.fixture
def mock_emitter_now(mocker):
    """Mock for the monotonic clock of the emitter."""
    return mocker.patch('src.shared_kernel.events.emitter._now')


@pytest.fixture
def mock_events_redis_from_url(mocker):
    """Mock for redis.asyncio.from_url as the emitter imports it."""
    return mocker.patch('src.shared_kernel.events.emitter.redis.from_url')


@pytest.fixture
def mock_emitter_settings(mocker):
    """Mock for get_settings in the emitter module."""
    return mocker.patch('src.shared_kernel.events.emitter.get_settings')


@pytest.fixture
def mock_events_file_upload(mocker):
    """Mock for RequestEvents.file_upload."""
    return mocker.patch(
        'src.shared_kernel.events.request_events.RequestEvents.file_upload',
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_events_file_download(mocker):
    """Mock for RequestEvents.file_download."""
    return mocker.patch(
        'src.shared_kernel.events.request_events.RequestEvents.file_download',
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_events_file_access_denied(mocker):
    """Mock for RequestEvents.file_access_denied."""
    return mocker.patch(
        'src.shared_kernel.events.request_events.'
        'RequestEvents.file_access_denied',
        new_callable=AsyncMock,
    )


# --- request_id fixtures ---


def _request_id_echo(request):
    """Echo the id the middleware stored."""
    return PlainTextResponse(request.state.request_id)


@pytest.fixture
def request_id_client():
    """Test client of an app with RequestIdMiddleware only."""
    app = Starlette(routes=[Route('/', _request_id_echo)])
    app.add_middleware(RequestIdMiddleware)
    return TestClient(app)


@pytest.fixture
def make_context_request():
    """Factory for mock requests of the events context.

    The headers are real Starlette Headers, case-insensitive as in
    production, so the tests may spell a name any way they like.
    """

    def _factory(
        headers=None,
        client_ip='127.0.0.1',
        *,
        has_client: bool = True,
        request_id=None,
    ):
        request = MagicMock(spec=Request)
        request.headers = Headers(headers or {})
        if has_client:
            request.client = MagicMock()
            request.client.host = client_ip
        else:
            request.client = None
        state = type('State', (), {})()
        if request_id is not None:
            state.request_id = request_id
        request.state = state
        return request

    return _factory
