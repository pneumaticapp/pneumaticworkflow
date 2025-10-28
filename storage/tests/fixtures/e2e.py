from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def e2e_client(test_client):
    """E2E test client."""
    return test_client


@pytest.fixture
def mock_auth_middleware(mocker) -> Iterator[MagicMock]:
    """Mock authentication middleware."""
    mock = mocker.patch(
        'src.shared_kernel.auth.token_auth.PneumaticToken.data',
    )
    mock.return_value = {'user_id': 1, 'account_id': 1}
    return mock


@pytest.fixture
def mock_http_client(mocker) -> Iterator[MagicMock]:
    """Mock HTTP client."""
    mock = mocker.patch(
        'src.infra.http_client.HttpClient.check_file_permission',
    )
    mock.return_value = True
    return mock


@pytest.fixture
def mock_storage_service(mocker) -> Iterator[AsyncMock]:
    """Mock storage service."""
    mock_session = mocker.patch('aioboto3.Session')
    mock_s3_client = AsyncMock()
    mock_session.return_value.client.return_value.__aenter__.return_value = (
        mock_s3_client
    )
    return mock_s3_client


@pytest.fixture
def mock_redis_client(mocker) -> Iterator[MagicMock]:
    """Mock Redis client."""
    mock = mocker.patch(
        'src.shared_kernel.auth.redis_client.RedisAuthClient.get',
    )
    mock.return_value = {'user_id': 1, 'account_id': 1}
    return mock


@pytest.fixture
def mock_db_session(mocker) -> Iterator[AsyncMock]:
    """Mock database session."""
    mock = mocker.patch('src.shared_kernel.di.container.get_db_session')
    mock_session = AsyncMock()
    mock.return_value = mock_session
    return mock_session


@pytest.fixture
def mock_unit_of_work(mocker) -> Iterator[AsyncMock]:
    """Mock unit of work."""
    mock = mocker.patch('src.shared_kernel.uow.unit_of_work.UnitOfWork')
    mock_uow = AsyncMock()
    mock.return_value = mock_uow
    return mock_uow


@pytest.fixture
def mock_upload_use_case(mocker) -> Iterator[AsyncMock]:
    """Mock upload use case."""
    mock = mocker.patch(
        'src.application.use_cases.file_upload.UploadFileUseCase.execute',
    )
    mock_response = MagicMock()
    mock_response.file_id = 'test-file-id-123'
    mock_response.public_url = 'http://localhost:8000/test-file-id-123'
    mock.return_value = mock_response
    return mock


@pytest.fixture
def mock_download_use_case(mocker) -> Iterator[AsyncMock]:
    """Mock download use case."""
    mock = mocker.patch(
        'src.application.use_cases.file_download.DownloadFileUseCase.execute',
    )
    mock_file_record = MagicMock()
    mock_file_record.file_id = 'test-file-id'
    mock_file_record.filename = 'test.txt'
    mock_file_record.content_type = 'text/plain'
    mock_file_record.size = 12

    mock.return_value = (mock_file_record, AsyncIteratorMock(b'test content'))
    return mock


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Authenticate headers."""
    return {'Authorization': 'Bearer valid-token'}


@pytest.fixture
def session_cookies() -> dict[str, str]:
    """Session cookies."""
    return {'token': 'session-token'}


@pytest.fixture
def mock_upload_response() -> MagicMock:
    """Mock upload response."""
    response = MagicMock()
    response.file_id = 'test-file-id-123'
    response.public_url = 'http://localhost:8000/test-file-id-123'
    return response


@pytest.fixture
def mock_file_record() -> MagicMock:
    """Mock file record."""
    record = MagicMock()
    record.file_id = 'test-file-id-123'
    record.filename = 'test_file.txt'
    record.content_type = 'text/plain'
    record.size = 1024
    return record


class AsyncIteratorMock:
    """Async iterator mock for file streams."""

    def __init__(self, content: bytes):
        self.content = content
        self._iter = iter([content])

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration from None


@pytest.fixture
def mock_download_response() -> tuple[MagicMock, AsyncIteratorMock]:
    """Mock download response."""
    record = MagicMock()
    record.file_id = 'test-file-id-123'
    record.filename = 'test_file.txt'
    record.content_type = 'text/plain'
    record.size = 1024

    content = AsyncIteratorMock(b'test file content')
    return record, content
