"""Tests for exception system."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.shared_kernel.exceptions import (
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
    create_error_response,
    register_exception_handlers,
)


class TestErrorCode:
    """Test ErrorCode class."""

    def test_error_code_creation(self):
        """Test error code creation."""
        error_code = ErrorCode(
            code='TEST_001',
            message='Test error',
            error_type=ErrorType.VALIDATION,
            http_status=400,
        )

        assert error_code.code == 'TEST_001'
        assert error_code.message == 'Test error'
        assert error_code.error_type == ErrorType.VALIDATION
        assert error_code.http_status == 400

    def test_error_code_with_details(self):
        """Test error code with details."""
        error_code = ErrorCode(
            code='TEST_002',
            message='Test error with details',
            error_type=ErrorType.DOMAIN,
            http_status=404,
            details='Additional details',
        )

        assert error_code.details == 'Additional details'


class TestErrorResponse:
    """Test ErrorResponse class."""

    def test_error_response_creation(self):
        """Test error response creation."""
        response = ErrorResponse(
            error_code='TEST_001',
            message='Test error',
            error_type='validation',
        )

        assert response.error_code == 'TEST_001'
        assert response.message == 'Test error'
        assert response.error_type == 'validation'

    def test_error_response_to_dict(self):
        """Test error response to dict conversion."""
        response = ErrorResponse(
            error_code='TEST_001',
            message='Test error',
            error_type='validation',
            details='Test details',
            timestamp='2023-01-01T00:00:00',
            request_id='test-123',
        )

        result = response.to_dict()

        assert result['error_code'] == 'TEST_001'
        assert result['message'] == 'Test error'
        assert result['error_type'] == 'validation'
        assert result['details'] == 'Test details'
        assert result['timestamp'] == '2023-01-01T00:00:00'
        assert result['request_id'] == 'test-123'

    def test_error_response_to_dict_without_optional_fields(self):
        """Test error response to dict without optional fields."""
        response = ErrorResponse(
            error_code='TEST_001',
            message='Test error',
            error_type='validation',
        )

        result = response.to_dict()

        assert 'details' not in result
        assert 'timestamp' not in result
        assert 'request_id' not in result


class TestBaseAppException:
    """Test BaseAppError class."""

    def test_base_app_exception_creation(self):
        """Test base app exception creation."""
        error_code = ErrorCode(
            code='TEST_001',
            message='Test error',
            error_type=ErrorType.VALIDATION,
            http_status=400,
        )

        exception = BaseAppError(error_code, details='Test details')

        assert exception.error_code == error_code
        assert exception.details == 'Test details'
        assert exception.http_status == 400
        assert exception.error_type == ErrorType.VALIDATION
        assert str(exception) == 'TEST_001: Test error'

    def test_base_app_exception_to_response(self):
        """Test base app exception to response."""
        error_code = ErrorCode(
            code='TEST_001',
            message='Test error',
            error_type=ErrorType.VALIDATION,
            http_status=400,
        )

        exception = BaseAppError(error_code, details='Test details')
        response = exception.to_response(
            timestamp='2023-01-01T00:00:00',
            request_id='test-123',
        )

        assert response.error_code == 'TEST_001'
        assert response.message == 'Test error'
        assert response.error_type == 'validation'
        assert response.details == 'Test details'
        assert response.timestamp == '2023-01-01T00:00:00'
        assert response.request_id == 'test-123'


class TestDomainExceptions:
    """Test domain exceptions."""

    def test_file_not_found_error(self):
        """Test file not found error."""
        exception = DomainFileNotFoundError('test-file-id')

        assert exception.error_code.code == 'FILE_001'
        assert 'test-file-id' in exception.error_code.message
        assert exception.http_status == 404
        assert exception.error_type == ErrorType.DOMAIN

    def test_file_access_denied_error(self):
        """Test file access denied error."""
        exception = FileAccessDeniedError('test-file-id', user_id=456)

        assert exception.error_code.code == 'FILE_002'
        assert 'test-file-id' in exception.error_code.message
        assert '456' in exception.error_code.message
        assert exception.http_status == 403
        assert exception.error_type == ErrorType.AUTHORIZATION

    def test_file_size_exceeded_error(self):
        """Test file size exceeded error."""
        exception = FileSizeExceededError(1000, 500)

        assert exception.error_code.code == 'FILE_003'
        assert '1000' in exception.error_code.message
        assert '500' in exception.error_code.message
        assert exception.http_status == 413
        assert exception.error_type == ErrorType.VALIDATION

    def test_storage_error(self):
        """Test storage error."""
        exception = StorageError.upload_failed('Upload failed')

        assert exception.error_code.code == 'STORAGE_002'
        assert (
            exception.error_code.message == 'Failed to upload file to storage'
        )
        assert exception.details == 'Upload failed: Upload failed'
        assert exception.http_status == 503
        assert exception.error_type == ErrorType.INFRASTRUCTURE


class TestDatabaseExceptions:
    """Test database exceptions."""

    def test_database_connection_error(self):
        """Test database connection error."""
        exception = DatabaseConnectionError('Connection failed')

        assert exception.error_code.code == 'DB_001'
        assert exception.error_code.message == 'Database connection failed'
        assert exception.details == 'Connection failed'
        assert exception.http_status == 503
        assert exception.error_type == ErrorType.INFRASTRUCTURE

    def test_database_operation_error(self):
        """Test database operation error."""
        exception = DatabaseOperationError('SELECT', 'Query failed')

        assert exception.error_code.code == 'DB_002'
        assert exception.error_code.message == 'Database operation failed'
        assert "Database operation 'SELECT' failed" in exception.details
        assert 'Query failed' in exception.details
        assert exception.http_status == 500
        assert exception.error_type == ErrorType.INFRASTRUCTURE

    def test_database_constraint_error(self):
        """Test database constraint error."""
        exception = DatabaseConstraintError(
            'unique_constraint', 'Duplicate key'
        )

        assert exception.error_code.code == 'DB_004'
        assert exception.error_code.message == 'Database constraint violation'
        assert 'unique_constraint' in exception.details
        assert 'Duplicate key' in exception.details
        assert exception.http_status == 409
        assert exception.error_type == ErrorType.DOMAIN

    def test_database_error_base_class(self):
        """Test database error base class."""
        exception = DatabaseError('DATABASE_CONNECTION_ERROR', 'Test error')

        assert exception.error_code.code == 'DB_001'
        assert exception.details == 'Test error'
        assert exception.http_status == 503


class TestExternalServiceExceptions:
    """Test external service exceptions."""

    def test_redis_connection_error(self):
        """Test Redis connection error."""
        exception = RedisConnectionError('Redis unavailable')

        assert exception.error_code.code == 'EXT_001'
        assert exception.error_code.message == 'Redis connection failed'
        assert exception.details == 'Redis unavailable'
        assert exception.http_status == 503
        assert exception.error_type == ErrorType.EXTERNAL_SERVICE

    def test_redis_operation_error(self):
        """Test Redis operation error."""
        exception = RedisOperationError('GET', 'Operation failed')

        assert exception.error_code.code == 'EXT_002'
        assert exception.error_code.message == 'Redis operation failed'
        assert "Redis operation 'GET' failed" in exception.details
        assert exception.http_status == 500
        assert exception.error_type == ErrorType.EXTERNAL_SERVICE

    def test_http_client_error(self):
        """Test HTTP client error."""
        exception = HttpClientError('http://example.com', 'Request failed')

        assert exception.error_code.code == 'EXT_003'
        assert exception.error_code.message == 'HTTP client request failed'
        assert 'http://example.com' in exception.details
        assert 'Request failed' in exception.details
        assert exception.http_status == 502
        assert exception.error_type == ErrorType.EXTERNAL_SERVICE

    def test_http_timeout_error(self):
        """Test HTTP timeout error."""
        exception = HttpTimeoutError(
            'http://example.com',
            30,
            'Timeout occurred',
        )

        assert exception.error_code.code == 'EXT_004'
        assert exception.error_code.message == 'HTTP request timeout'
        assert 'http://example.com' in exception.details
        assert '30s' in exception.details
        assert exception.http_status == 504
        assert exception.error_type == ErrorType.EXTERNAL_SERVICE

    def test_external_service_error_base_class(self):
        """Test external service error base class."""
        exception = ExternalServiceError(
            'REDIS_CONNECTION_ERROR', 'Test error'
        )

        assert exception.error_code.code == 'EXT_001'
        assert exception.details == 'Test error'
        assert exception.http_status == 503


class TestPermissionExceptions:
    """Test permission exceptions."""

    def test_permission_denied_error(self):
        """Test permission denied error."""
        exception = PermissionDeniedError('Access denied')

        assert exception.error_code.code == 'PERM_001'
        assert exception.error_code.message == 'Permission denied'
        assert exception.details == 'Access denied'
        assert exception.http_status == 403
        assert exception.error_type == ErrorType.AUTHORIZATION


class TestAuthExceptions:
    """Test authentication exceptions."""

    def test_authentication_error(self):
        """Test authentication error."""
        exception = AuthenticationError('Auth failed')

        assert exception.error_code.code == 'AUTH_001'
        assert exception.error_code.message == 'Authentication failed'
        assert exception.details == 'Auth failed'
        assert exception.http_status == 401
        assert exception.error_type == ErrorType.AUTHENTICATION


class TestExceptionHandlers:
    """Test exception handlers."""

    def test_create_error_response(self):
        """Test create error response."""
        response = create_error_response(
            error_code='TEST_001',
            message='Test error',
            error_type='validation',
            details='Test details',
            timestamp='2023-01-01T00:00:00',
        )

        assert response['error_code'] == 'TEST_001'
        assert response['message'] == 'Test error'
        assert response['error_type'] == 'validation'
        assert response['details'] == 'Test details'
        assert response['timestamp'] == '2023-01-01T00:00:00'

    def test_register_exception_handlers(self):
        """Test register universal exception handlers."""
        app = FastAPI()
        register_exception_handlers(app)

        # Check that handlers are registered
        assert len(app.exception_handlers) > 0

        # Check for main handlers
        handlers = list(app.exception_handlers.keys())
        assert BaseAppError in handlers
        assert Exception in handlers


class TestExceptionHandlerIntegration:
    """Test exception handler integration."""

    def test_file_not_found_handler_integration(self):
        """Test file not found handler integration."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get('/test')
        async def test_endpoint():
            file_id = 'test-file-id'
            raise DomainFileNotFoundError(file_id)

        client = TestClient(app)
        response = client.get('/test')

        assert response.status_code == 404
        data = response.json()
        assert data['error_code'] == 'FILE_001'
        assert data['error_type'] == 'domain'
        assert 'test-file-id' in data['message']

    def test_authentication_error_handler_integration(self):
        """Test authentication error handler integration."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get('/test')
        async def test_endpoint():
            raise AuthenticationError

        client = TestClient(app)
        response = client.get('/test')

        assert response.status_code == 401
        data = response.json()
        assert data['error_code'] == 'AUTH_001'
        assert data['error_type'] == 'authentication'
