from unittest.mock import AsyncMock, MagicMock

import pytest


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
def e2e_client(test_client):
    """E2E test client."""
    return test_client


@pytest.fixture
def mock_auth_middleware(mocker) -> MagicMock:
    """Mock authentication middleware."""
    mock_token_data = mocker.patch(
        'src.shared_kernel.auth.token_auth.PneumaticToken.data',
    )
    mock_token_data.return_value = {
        'user_id': 1,
        'account_id': 1,
    }

    mock_redis_get = mocker.patch(
        'src.shared_kernel.auth.redis_client.RedisAuthClient.get',
    )
    mock_redis_get.return_value = {
        'user_id': 1,
        'account_id': 1,
    }

    return mock_token_data


@pytest.fixture
def mock_http_client(mocker) -> AsyncMock:
    """Mock HTTP client for e2e tests."""
    mock = mocker.patch(
        'src.infra.http_client.HttpClient.check_file_permission',
        new_callable=AsyncMock,
    )
    mock.return_value = True
    return mock


@pytest.fixture
def mock_storage_service(mocker) -> AsyncMock:
    """Mock storage service for e2e tests."""
    mock_session = mocker.patch('aioboto3.Session')
    mock_s3_client = AsyncMock()
    mock_session.return_value.client.return_value.__aenter__.return_value = (
        mock_s3_client
    )
    return mock_s3_client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Authenticate headers."""
    return {'Authorization': 'Bearer valid-token'}


@pytest.fixture
def mock_upload_response() -> MagicMock:
    """Mock upload response."""
    response = MagicMock()
    response.file_id = '12345678-1234-5678-1234-567812345679'
    response.public_url = (
        'http://localhost:8000/12345678-1234-5678-1234-567812345679'
    )
    return response


@pytest.fixture
def mock_download_response() -> tuple[
    MagicMock,
    AsyncIteratorMock,
]:
    """Mock download response."""
    record = MagicMock()
    record.file_id = '12345678-1234-5678-1234-567812345679'
    record.filename = 'test_file.txt'
    record.content_type = 'text/plain'
    record.size = 1024
    record.user_id = 1
    record.account_id = 1

    content = AsyncIteratorMock(b'test file content')
    return record, content
