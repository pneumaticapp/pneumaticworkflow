from unittest.mock import AsyncMock

import pytest

from tests.fixtures.common import (
    event_loop,
    mock_anonymous_user,
    mock_auth_user,
    mock_http_client,
    mock_repository,
    mock_storage_service,
    mock_user,
    sample_download_query,
    sample_file_content,
    sample_file_record,
    sample_large_file_content,
    sample_upload_command,
    test_client,
    test_settings,
)
from tests.fixtures.e2e import (
    AsyncIteratorMock,
    auth_headers,
    e2e_client,
    mock_auth_middleware,
    mock_db_session,
    mock_download_response,
    mock_download_use_case,
    mock_file_record,
    mock_redis_client,
    mock_unit_of_work,
    mock_upload_response,
    mock_upload_use_case,
    session_cookies,
)
from tests.fixtures.integration import (
    async_session,
    test_engine,
    test_session_factory,
)

pytest_plugins = ['pytest_mock']


@pytest.fixture
def mock_upload_use_case_execute(mocker):
    """Mock for UploadFileUseCase.execute."""
    return mocker.patch(
        'src.application.use_cases.file_upload.UploadFileUseCase.execute',
    )


@pytest.fixture
def mock_download_use_case_execute(mocker):
    """Mock for DownloadFileUseCase.execute."""
    return mocker.patch(
        'src.application.use_cases.file_download.DownloadFileUseCase.execute',
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


# Export all fixtures
__all__ = [
    'AsyncIteratorMock',
    'async_session',
    'auth_headers',
    'e2e_client',
    'event_loop',
    'mock_aioboto3_session',
    'mock_anonymous_user',
    'mock_auth_middleware',
    'mock_auth_middleware_authenticate_token',
    'mock_auth_middleware_pneumatic_token_data',
    'mock_auth_user',
    'mock_db_session',
    'mock_download_response',
    'mock_download_use_case',
    'mock_download_use_case_execute',
    'mock_file_record',
    'mock_get_db_session',
    'mock_get_redis_client',
    'mock_get_settings',
    'mock_http_client',
    'mock_http_client_check_permission',
    'mock_pneumatic_token_data',
    'mock_redis_auth_client_get',
    'mock_redis_client',
    'mock_redis_from_url',
    'mock_repository',
    'mock_storage_service',
    'mock_unit_of_work',
    'mock_upload_response',
    'mock_upload_use_case',
    'mock_upload_use_case_execute',
    'mock_user',
    'sample_download_query',
    'sample_file_content',
    'sample_file_record',
    'sample_large_file_content',
    'sample_upload_command',
    'session_cookies',
    'test_client',
    'test_engine',
    'test_session_factory',
    'test_settings',
]
