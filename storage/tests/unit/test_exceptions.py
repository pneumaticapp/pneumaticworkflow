"""Tests for exception system."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.shared_kernel.exceptions import (
    VALIDATION_ERROR_CODES,
    AuthenticationError,
    BaseAppError,
    DatabaseConnectionError,
    DatabaseConstraintError,
    DatabaseError,
    DatabaseOperationError,
    DomainFileNotFoundError,
    ErrorCode,
    ErrorResponse,
    ErrorType,
    ExternalServiceError,
    FileAccessDeniedError,
    FileSizeExceededError,
    HttpClientError,
    HttpTimeoutError,
    PermissionDeniedError,
    RedisConnectionError,
    RedisOperationError,
    StorageError,
    register_exception_handlers,
)

# --- ErrorCode ---


def test_error_code__create__ok():
    # act
    error_code = ErrorCode(
        code='TEST_001',
        message='Test error',
        error_type=ErrorType.VALIDATION,
        http_status=422,
    )

    # assert
    assert error_code.code == 'TEST_001'
    assert error_code.message == 'Test error'
    assert error_code.error_type == ErrorType.VALIDATION
    assert error_code.http_status == 422


def test_error_code__with_details__ok():
    # act
    error_code = ErrorCode(
        code='TEST_002',
        message='Test error with details',
        error_type=ErrorType.DOMAIN,
        http_status=404,
        details='Additional details',
    )

    # assert
    assert error_code.details == 'Additional details'


# --- ErrorResponse ---


def test_error_response__create__ok():
    # act
    response = ErrorResponse(
        code='TEST_001',
        message='Test error',
    )

    # assert
    assert response.code == 'TEST_001'
    assert response.message == 'Test error'


def test_error_response__to_dict__all_fields():
    # arrange
    response = ErrorResponse(
        code='TEST_001',
        message='Test error',
        details='Test details',
    )

    # act
    result = response.to_dict()

    # assert
    assert result['code'] == 'TEST_001'
    assert result['message'] == 'Test error'
    assert result['details'] == {'reason': 'Test details'}


def test_error_response__to_dict__no_optional():
    # arrange
    response = ErrorResponse(
        code='TEST_001',
        message='Test error',
    )

    # act
    result = response.to_dict()

    # assert
    assert 'details' not in result
    assert 'error_type' not in result
    assert 'timestamp' not in result
    assert 'request_id' not in result


def test_error_response__to_dict__details_as_dict():
    """Details should be serialized as {reason: str} for backend compat."""
    # arrange
    response = ErrorResponse(
        code='FILE_003',
        message='File size exceeds limit',
        details='File size 200MB exceeds limit 100MB',
    )

    # act
    result = response.to_dict()

    # assert
    assert result['details'] == {
        'reason': 'File size 200MB exceeds limit 100MB',
    }


def test_error_response__to_dict__backend_compatible_keys():
    """Response format must match Django/DRF: {code, message, details?}."""
    # arrange
    response = ErrorResponse(
        code='VAL_001',
        message='Invalid file size',
        details='Size must be positive',
    )

    # act
    result = response.to_dict()

    # assert - must have exactly these keys
    assert set(result.keys()) == {'code', 'message', 'details'}
    assert result['code'] == 'VAL_001'
    assert result['message'] == 'Invalid file size'
    assert result['details'] == {'reason': 'Size must be positive'}


def test_error_response__to_dict__no_error_type_in_output():
    """error_type must NOT appear in serialized output."""
    # arrange
    response = ErrorResponse(
        code='AUTH_001',
        message='Auth failed',
    )

    # act
    result = response.to_dict()

    # assert
    assert 'error_type' not in result
    assert 'timestamp' not in result
    assert 'request_id' not in result


def test_error_response__to_dict__no_details__key_absent():
    """When details is None, details key should not be in dict."""
    # arrange
    response = ErrorResponse(
        code='FILE_001',
        message='File not found',
    )

    # act
    result = response.to_dict()

    # assert
    assert 'details' not in result
    assert set(result.keys()) == {'code', 'message'}


# --- BaseAppError ---


def test_base_app_error__create__ok():
    # arrange
    error_code = ErrorCode(
        code='TEST_001',
        message='Test error',
        error_type=ErrorType.VALIDATION,
        http_status=422,
    )

    # act
    exception = BaseAppError(error_code, details='Test details')

    # assert
    assert exception.error_code == error_code
    assert exception.details == 'Test details'
    assert exception.http_status == 422
    assert exception.error_type == ErrorType.VALIDATION
    assert str(exception) == 'TEST_001: Test error'


def test_base_app_error__to_response__ok():
    # arrange
    error_code = ErrorCode(
        code='TEST_001',
        message='Test error',
        error_type=ErrorType.VALIDATION,
        http_status=422,
    )
    exception = BaseAppError(error_code, details='Test details')

    # act
    response = exception.to_response()

    # assert
    assert response.code == 'TEST_001'
    assert response.message == 'Test error'
    assert response.details == 'Test details'


def test_base_app_error__to_response__to_dict__backend_format():
    """Full pipeline: BaseAppError -> to_response() -> to_dict()."""
    # arrange
    error_code = ErrorCode(
        code='FILE_003',
        message='File size exceeds limit',
        error_type=ErrorType.VALIDATION,
        http_status=413,
    )
    exception = BaseAppError(error_code, details='200MB exceeds 100MB')

    # act
    result = exception.to_response().to_dict()

    # assert
    assert result == {
        'code': 'FILE_003',
        'message': 'File size exceeds limit',
        'details': {'reason': '200MB exceeds 100MB'},
    }


def test_base_app_error__to_response__no_details():
    """to_response() without details omits details key."""
    # arrange
    error_code = ErrorCode(
        code='AUTH_001',
        message='Authentication failed',
        error_type=ErrorType.AUTHENTICATION,
        http_status=401,
    )
    exception = BaseAppError(error_code)

    # act
    result = exception.to_response().to_dict()

    # assert
    assert result == {
        'code': 'AUTH_001',
        'message': 'Authentication failed',
    }
    assert 'details' not in result


# --- Domain exceptions ---


def test_file_not_found__create__ok():
    # act
    exc = DomainFileNotFoundError(
        file_id=('12345678-1234-5678-1234-567812345678'),
    )

    # assert
    assert exc.error_code.code == 'FILE_001'
    assert "'12345678-1234-5678-1234-567812345678'" in exc.error_code.message
    assert exc.http_status == 404
    assert exc.error_type == ErrorType.DOMAIN


def test_file_not_found__with_account__ok():
    # act
    exc = DomainFileNotFoundError(
        file_id=('12345678-1234-5678-1234-567812345678'),
        account_id=123,
    )

    # assert
    assert exc.error_code.code == 'FILE_001'
    assert 'account 123' in exc.error_code.message
    assert exc.http_status == 404


def test_file_access_denied__create__ok():
    # act
    exc = FileAccessDeniedError(
        file_id=('12345678-1234-5678-1234-567812345678'),
        user_id=456,
    )

    # assert
    assert exc.error_code.code == 'FILE_002'
    assert 'User 456' in exc.error_code.message
    assert exc.http_status == 403
    assert exc.error_type == ErrorType.AUTHORIZATION


def test_file_access_denied__none_user__anonymous():
    # act
    exc = FileAccessDeniedError(
        file_id=('12345678-1234-5678-1234-567812345678'),
        user_id=None,
    )

    # assert
    assert exc.error_code.code == 'FILE_002'
    assert 'anonymous' in exc.error_code.message
    assert exc.http_status == 403


def test_file_size_exceeded__create__ok():
    # act
    exc = FileSizeExceededError(
        size=1000,
        max_size=500,
    )

    # assert
    assert exc.error_code.code == 'FILE_003'
    assert '1000' in exc.error_code.message
    assert '500' in exc.error_code.message
    assert exc.http_status == 413
    assert exc.error_type == ErrorType.VALIDATION


# --- StorageError ---


def test_storage__upload_failed__ok():
    # act
    exc = StorageError.upload_failed('Connection timeout')

    # assert
    assert exc.error_code.code == 'STORAGE_002'
    assert exc.details == 'Upload failed: Connection timeout'
    assert exc.http_status == 503


def test_storage__download_failed__ok():
    # act
    exc = StorageError.download_failed('File corrupted')

    # assert
    assert exc.error_code.code == 'STORAGE_003'
    assert exc.details == 'Download failed: File corrupted'
    assert exc.http_status == 503


def test_storage__bucket_create_failed__ok():
    # act
    exc = StorageError.bucket_create_failed(
        'Insufficient permissions',
    )

    # assert
    assert exc.error_code.code == 'STORAGE_004'
    assert 'Insufficient permissions' in exc.details
    assert exc.http_status == 503


def test_storage__file_not_found__ok():
    # act
    exc = StorageError.file_not_found_in_storage(
        file_path='path/to/file.txt',
        bucket_name='my-bucket',
    )

    # assert
    assert exc.error_code.code == 'STORAGE_005'
    assert 'path/to/file.txt' in exc.details
    assert 'my-bucket' in exc.details
    assert exc.http_status == 404


def test_storage__file_not_found__with_details():
    # act
    exc = StorageError.file_not_found_in_storage(
        file_path='doc.pdf',
        bucket_name='bucket-1',
        details='S3 returned 404',
    )

    # assert
    assert exc.error_code.code == 'STORAGE_005'
    assert 'doc.pdf' in exc.details
    assert 'bucket-1' in exc.details
    assert 'S3 returned 404' in exc.details


def test_storage__delete_failed__ok():
    # act
    exc = StorageError.delete_failed('Access denied')

    # assert
    assert exc.error_code.code == 'STORAGE_006'
    assert exc.details == 'Delete failed: Access denied'
    assert exc.http_status == 503


def test_storage__delete_no_details__unknown():
    # act
    exc = StorageError.delete_failed()

    # assert
    assert exc.details == 'Delete failed: Unknown error'


def test_storage__upload_no_details__unknown():
    # act
    exc = StorageError.upload_failed()

    # assert
    assert exc.details == 'Upload failed: Unknown error'


def test_storage__download_no_details__unknown():
    # act
    exc = StorageError.download_failed()

    # assert
    assert exc.details == 'Download failed: Unknown error'


def test_storage__bucket_no_details__unknown():
    # act
    exc = StorageError.bucket_create_failed()

    # assert
    assert exc.details == ('Bucket creation failed: Unknown error')


def test_storage__invalid_key__raise_key_error():
    # act
    with pytest.raises(KeyError):
        StorageError('NONEXISTENT_KEY')


# --- Database exceptions ---


def test_db_connection_error__create__ok():
    # act
    exc = DatabaseConnectionError('Connection failed')

    # assert
    assert exc.error_code.code == 'DB_001'
    assert exc.details == 'Connection failed'
    assert exc.http_status == 503


def test_db_operation_error__create__ok():
    # act
    exc = DatabaseOperationError(
        operation='SELECT',
        details='Query failed',
    )

    # assert
    assert exc.error_code.code == 'DB_002'
    assert "Database operation 'SELECT' failed" in exc.details
    assert 'Query failed' in exc.details
    assert exc.http_status == 500


def test_db_constraint_error__create__ok():
    # act
    exc = DatabaseConstraintError(
        constraint='unique_constraint',
        details='Duplicate key',
    )

    # assert
    assert exc.error_code.code == 'DB_004'
    assert 'unique_constraint' in exc.details
    assert 'Duplicate key' in exc.details
    assert exc.http_status == 409


def test_db_error__base_class__ok():
    # act
    exc = DatabaseError(
        error_code_key='DATABASE_CONNECTION_ERROR',
        details='Test error',
    )

    # assert
    assert exc.error_code.code == 'DB_001'
    assert exc.details == 'Test error'
    assert exc.http_status == 503


# --- External service exceptions ---


def test_redis_connection_error__create__ok():
    # act
    exc = RedisConnectionError('Redis unavailable')

    # assert
    assert exc.error_code.code == 'EXT_001'
    assert exc.details == 'Redis unavailable'
    assert exc.http_status == 503


def test_redis_operation_error__create__ok():
    # act
    exc = RedisOperationError(
        operation='GET',
        details='Operation failed',
    )

    # assert
    assert exc.error_code.code == 'EXT_002'
    assert "Redis operation 'GET' failed" in exc.details
    assert exc.http_status == 500


def test_http_client_error__create__ok():
    # act
    exc = HttpClientError(
        'http://example.com',
        details='Request failed',
    )

    # assert
    assert exc.error_code.code == 'EXT_003'
    assert "'http://example.com'" in exc.details
    assert exc.http_status == 502


def test_http_client_error__with_status__ok():
    # act
    exc = HttpClientError(
        'http://example.com',
        status_code=404,
        details='Not found',
    )

    # assert
    assert exc.error_code.code == 'EXT_003'
    assert 'status 404' in exc.details
    assert exc.http_status == 502


def test_http_timeout_error__create__ok():
    # act
    exc = HttpTimeoutError(
        url='http://example.com',
        timeout=30,
        details='Timeout occurred',
    )

    # assert
    assert exc.error_code.code == 'EXT_004'
    assert '30s' in exc.details
    assert exc.http_status == 504


def test_external_service__base_class__ok():
    # act
    exc = ExternalServiceError(
        error_code_key='REDIS_CONNECTION_ERROR',
        details='Test error',
    )

    # assert
    assert exc.error_code.code == 'EXT_001'
    assert exc.details == 'Test error'
    assert exc.http_status == 503


# --- Permission / Validation / Auth ---


def test_permission_denied__create__ok():
    # act
    exc = PermissionDeniedError('Access denied')

    # assert
    assert exc.error_code.code == 'PERM_001'
    assert exc.details == 'Access denied'
    assert exc.http_status == 403


def test_validation__invalid_file_size__ok():
    # arrange
    error_code = VALIDATION_ERROR_CODES['INVALID_FILE_SIZE']

    # act
    exc = BaseAppError(
        error_code=error_code,
        details='File size must be positive',
    )

    # assert
    assert exc.error_code.code == 'VAL_001'
    assert exc.details == 'File size must be positive'
    assert exc.http_status == 422


def test_authentication_error__create__ok():
    # act
    exc = AuthenticationError('Auth failed')

    # assert
    assert exc.error_code.code == 'AUTH_001'
    assert exc.details == 'Auth failed'
    assert exc.http_status == 401


def test_register_handlers__registers__ok():
    # arrange
    app = FastAPI()

    # act
    register_exception_handlers(app)

    # assert
    handlers = list(app.exception_handlers.keys())
    assert BaseAppError in handlers
    assert Exception in handlers


# --- Handler integration ---


def test_handler__file_not_found__404():
    # arrange
    app = FastAPI()
    register_exception_handlers(app)

    @app.get('/test')
    async def test_endpoint():
        raise DomainFileNotFoundError(
            '12345678-1234-5678-1234-567812345678',
        )

    client = TestClient(app)

    # act
    response = client.get('/test')

    # assert
    assert response.status_code == 404
    data = response.json()
    assert data['code'] == 'FILE_001'
    assert 'error_type' not in data
    assert 'timestamp' not in data
    assert 'request_id' not in data


def test_handler__auth_error__401():
    # arrange
    app = FastAPI()
    register_exception_handlers(app)

    @app.get('/test')
    async def test_endpoint():
        raise AuthenticationError

    client = TestClient(app)

    # act
    response = client.get('/test')

    # assert
    assert response.status_code == 401
    data = response.json()
    assert data['code'] == 'AUTH_001'
    assert 'error_type' not in data
    assert 'timestamp' not in data
    assert 'request_id' not in data


def test_handler__domain_error__backend_format():
    """Domain error response: {code, message}, no error_type."""
    # arrange
    app = FastAPI()
    register_exception_handlers(app)

    @app.get('/test')
    async def test_endpoint():
        raise DomainFileNotFoundError('test-id')

    client = TestClient(app)

    # act
    response = client.get('/test')
    data = response.json()

    # assert
    assert response.status_code == 404
    assert data['code'] == 'FILE_001'
    assert 'message' in data
    assert 'error_type' not in data
    assert 'timestamp' not in data
    assert 'request_id' not in data


def test_handler__validation_error__details_as_dict():
    """Validation error details should be {reason: str}."""
    # arrange
    app = FastAPI()
    register_exception_handlers(app)

    @app.get('/test')
    async def test_endpoint():
        raise FileSizeExceededError(size=200, max_size=100)

    client = TestClient(app)

    # act
    response = client.get('/test')
    data = response.json()

    # assert
    assert response.status_code == 413
    assert data['code'] == 'FILE_003'
    if 'details' in data:
        assert isinstance(data['details'], dict)
        assert 'reason' in data['details']


def test_handler__unhandled_exception__backend_format():
    """Generic 500 errors must also follow {code, message} format."""
    # arrange

    mock_settings = MagicMock()
    mock_settings.DEBUG = False

    app = FastAPI()
    register_exception_handlers(app)

    @app.get('/test')
    async def test_endpoint():
        raise RuntimeError('unexpected')

    client = TestClient(app, raise_server_exceptions=False)

    # act
    with patch(
        'src.shared_kernel.exceptions.exception_handler.get_settings',
        return_value=mock_settings,
    ) as get_settings_mock:
        response = client.get('/test')
    data = response.json()

    # assert
    assert response.status_code == 500
    assert 'code' in data
    assert 'message' in data
    assert 'error_type' not in data
    assert 'timestamp' not in data
    assert 'request_id' not in data
    get_settings_mock.assert_called()


def test_handler__permission_error__backend_format():
    """Permission error: {code: PERM_001, ...}."""
    # arrange
    app = FastAPI()
    register_exception_handlers(app)

    @app.get('/test')
    async def test_endpoint():
        raise PermissionDeniedError('forbidden')

    client = TestClient(app)

    # act
    response = client.get('/test')
    data = response.json()

    # assert
    assert response.status_code == 403
    assert data['code'] == 'PERM_001'
    assert 'error_type' not in data


def test_handler__storage_error__backend_format():
    """Storage error: infrastructure errors masked in prod."""
    # arrange
    app = FastAPI()
    register_exception_handlers(app)

    @app.get('/test')
    async def test_endpoint():
        raise StorageError.upload_failed('timeout')

    client = TestClient(app)

    # act
    response = client.get('/test')
    data = response.json()

    # assert
    assert response.status_code == 503
    assert data['code'] == 'STORAGE_002'
    assert 'error_type' not in data
    assert 'timestamp' not in data
    assert 'request_id' not in data


def test_handler__file_access_denied__backend_format():
    """File access denied: {code: FILE_002}."""
    # arrange
    app = FastAPI()
    register_exception_handlers(app)

    @app.get('/test')
    async def test_endpoint():
        raise FileAccessDeniedError(
            file_id='test-file',
            user_id=1,
        )

    client = TestClient(app)

    # act
    response = client.get('/test')
    data = response.json()

    # assert
    assert response.status_code == 403
    assert data['code'] == 'FILE_002'
    assert 'error_type' not in data


def test_handler__response_keys__only_code_message_details():
    """All error responses must have only {code, message} or
    {code, message, details} — no extra fields."""
    # arrange
    app = FastAPI()
    register_exception_handlers(app)

    @app.get('/test')
    async def test_endpoint():
        raise DomainFileNotFoundError('test-id')

    client = TestClient(app)

    # act
    data = client.get('/test').json()

    # assert
    allowed_keys = {'code', 'message', 'details'}
    assert set(data.keys()).issubset(allowed_keys)


def test_handler__browser_get_404__redirect_to_error_page():
    """Browser GET → 404 → redirect to /error/."""
    # arrange
    app = FastAPI()
    register_exception_handlers(app)

    @app.get('/test')
    async def test_endpoint():
        raise DomainFileNotFoundError('test-id')

    client = TestClient(app, follow_redirects=False)

    mock_settings = MagicMock()
    mock_settings.FRONTEND_URL = 'https://app.example.com'

    # act
    with patch(
        'src.shared_kernel.browser_utils.get_settings',
        return_value=mock_settings,
    ) as get_settings_mock:
        response = client.get(
            '/test',
            headers={'accept': 'text/html'},
        )

    # assert
    assert response.status_code == 302
    assert response.headers['location'] == 'https://app.example.com/error/'
    get_settings_mock.assert_called()


def test_handler__browser_get_403__redirect_to_error_page():
    """Browser GET → 403 → redirect to /error/."""
    # arrange
    app = FastAPI()
    register_exception_handlers(app)

    @app.get('/test')
    async def test_endpoint():
        raise FileAccessDeniedError(
            file_id='test-file',
            user_id=1,
        )

    client = TestClient(app, follow_redirects=False)

    mock_settings = MagicMock()
    mock_settings.FRONTEND_URL = 'https://app.example.com'

    # act
    with patch(
        'src.shared_kernel.browser_utils.get_settings',
        return_value=mock_settings,
    ) as get_settings_mock:
        response = client.get(
            '/test',
            headers={'accept': 'text/html'},
        )

    # assert
    assert response.status_code == 302
    assert response.headers['location'] == 'https://app.example.com/error/'
    get_settings_mock.assert_called()


def test_handler__browser_get_401__redirect_to_login():
    """Browser GET → 401 → redirect to login with redirectUrl."""
    # arrange
    app = FastAPI()
    register_exception_handlers(app)

    @app.get('/test')
    async def test_endpoint():
        raise AuthenticationError

    client = TestClient(app, follow_redirects=False)

    mock_settings = MagicMock()
    mock_settings.FRONTEND_URL = 'https://app.example.com'

    # act
    with patch(
        'src.shared_kernel.browser_utils.get_settings',
        return_value=mock_settings,
    ) as get_settings_mock:
        response = client.get(
            '/test',
            headers={'accept': 'text/html'},
        )

    # assert
    assert response.status_code == 302
    location = response.headers['location']
    assert 'auth/signin' in location
    assert 'redirectUrl=' in location
    get_settings_mock.assert_called()


def test_handler__browser_get_500__redirect_to_error_page():
    """Browser GET → 500 → redirect to /error/."""
    # arrange
    app = FastAPI()
    register_exception_handlers(app)

    @app.get('/test')
    async def test_endpoint():
        raise RuntimeError('unexpected')

    client = TestClient(
        app,
        raise_server_exceptions=False,
        follow_redirects=False,
    )

    mock_settings = MagicMock()
    mock_settings.FRONTEND_URL = 'https://app.example.com'

    # act
    with patch(
        'src.shared_kernel.browser_utils.get_settings',
        return_value=mock_settings,
    ) as browser_settings_mock:
        response = client.get(
            '/test',
            headers={'accept': 'text/html'},
        )

    # assert
    assert response.status_code == 302
    assert response.headers['location'] == 'https://app.example.com/error/'
    browser_settings_mock.assert_called()


def test_handler__api_get_404__returns_json():
    """API GET (Accept: json) → 404 → still returns JSON, not redirect."""
    # arrange
    app = FastAPI()
    register_exception_handlers(app)

    @app.get('/test')
    async def test_endpoint():
        raise DomainFileNotFoundError('test-id')

    client = TestClient(app)

    # act
    response = client.get(
        '/test',
        headers={'accept': 'application/json'},
    )

    # assert
    assert response.status_code == 404
    data = response.json()
    assert data['code'] == 'FILE_001'
