import asyncio
from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from fastapi.testclient import TestClient
from src.application.dto import DownloadFileQuery, UploadFileCommand
from src.domain.entities import FileRecord
from src.main import app
from src.shared_kernel.config import Settings


@pytest.fixture(scope='session')
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Test settings"""
    return Settings(
        DEBUG=True,
        CONFIG='Test',
        POSTGRES_DB='test_db',
        POSTGRES_HOST='localhost',
        POSTGRES_PORT=5432,
        STORAGE_TYPE='local',
        MAX_FILE_SIZE=1024 * 1024,  # 1MB
        FASTAPI_BASE_URL='http://localhost:8000',
    )


@pytest.fixture
def test_client() -> TestClient:
    """Test client"""
    return TestClient(app)


@pytest.fixture
def sample_file_content() -> bytes:
    """Sample file content"""
    return b'test file content'


@pytest.fixture
def sample_large_file_content() -> bytes:
    """Sample large file content"""
    return b'x' * (256 * 1024)  # 256KB


@pytest.fixture
def sample_file_record() -> FileRecord:
    """Sample file record"""
    return FileRecord(
        file_id='test-file-id-123',
        filename='test_file.txt',
        content_type='text/plain',
        size=1024,
        user_id=1,
        account_id=1,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_upload_command() -> UploadFileCommand:
    """Sample upload command"""
    return UploadFileCommand(
        file_content=b'test file content',
        filename='test_file.txt',
        content_type='text/plain',
        size=1024,
        user_id=1,
        account_id=1,
    )


@pytest.fixture
def sample_download_query() -> DownloadFileQuery:
    """Sample download query"""
    return DownloadFileQuery(
        file_id='test-file-id-123',
        user_id=1,
    )


@pytest.fixture
def mock_user() -> MagicMock:
    """Mock user"""
    mock = MagicMock()
    mock.user_id = 1
    mock.account_id = 1
    mock.is_authenticated = True
    return mock


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user"""
    mock = MagicMock()
    mock.user_id = 1
    mock.account_id = 1
    mock.is_authenticated = True
    return mock


@pytest.fixture
def mock_anonymous_user():
    """Mock anonymous user"""
    mock = MagicMock()
    mock.user_id = None
    mock.account_id = None
    mock.is_authenticated = False
    return mock


@pytest.fixture
def mock_http_client() -> AsyncMock:
    """Mock HTTP client"""
    mock = AsyncMock()
    mock.check_file_permission.return_value = True
    return mock


@pytest.fixture
def mock_storage_service():
    """Mock storage service"""
    mock = AsyncMock()
    # get_storage_path - synchronous method, not AsyncMock
    mock.get_storage_path = Mock(return_value=('test-bucket', 'test-file-id'))
    return mock


@pytest.fixture
def mock_repository():
    """Mock file repository"""
    return AsyncMock()
