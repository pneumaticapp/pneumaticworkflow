"""Root conftest — registers fixture plugins and defines mock fixtures."""

from unittest.mock import AsyncMock

import pytest

pytest_plugins = [
    'tests.fixtures.common',
    'tests.fixtures.integration',
    'tests.fixtures.unit',
]


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
def mock_get_settings(mocker):
    """Mock for get_settings."""
    return mocker.patch('src.shared_kernel.auth.token_auth.get_settings')


@pytest.fixture
def mock_get_redis_client(mocker):
    """Mock for get_redis_client."""
    return mocker.patch('src.shared_kernel.auth.token_auth.get_redis_client')


@pytest.fixture
def mock_httpx_post(mocker):
    """Mock for httpx.AsyncClient.post."""
    return mocker.patch('httpx.AsyncClient.post')


@pytest.fixture
def mock_aioboto3_session(mocker):
    """Mock for aioboto3.Session."""
    return mocker.patch('aioboto3.Session')


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
    return mocker.patch('src.shared_kernel.di.container.get_db_session')


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
