from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Request, Response
from src.shared_kernel.auth.user_types import UserType
from src.shared_kernel.exceptions import AuthenticationError
from src.shared_kernel.middleware.auth_middleware import (
    AuthenticationMiddleware,
    AuthUser,
)


class TestAuthUser:
    """Test AuthUser class"""

    def test_create__valid_data__ok(self):
        """Test user creation"""
        user = AuthUser(
            auth_type=UserType.AUTHENTICATED,
            user_id=1,
            account_id=2,
        )

        assert user.user_id == 1
        assert user.account_id == 2
        assert user.is_anonymous is False


class TestAuthenticationMiddleware:
    """Test AuthenticationMiddleware"""

    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI app"""
        app = Mock()
        return app

    @pytest.fixture
    def middleware(self, mock_app):
        """Authentication middleware instance"""
        return AuthenticationMiddleware(mock_app, require_auth=True)

    @pytest.fixture
    def middleware_no_auth(self, mock_app):
        """Middleware without required auth"""
        return AuthenticationMiddleware(mock_app, require_auth=False)

    @pytest.fixture
    def mock_request(self):
        """Mock request"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.cookies = {}
        return request

    @pytest.fixture
    def mock_call_next(self):
        """Mock call_next function"""

        async def mock_call_next(request):
            return Response(content='OK', status_code=200)

        return mock_call_next

    @pytest.mark.asyncio
    async def test_authenticate_token__valid_token__return_user(
        self,
        middleware,
    ):
        """Test successful token authentication"""
        # Arrange
        token = 'valid-token'
        expected_user = AuthUser(
            auth_type=UserType.AUTHENTICATED,
            user_id=1,
            account_id=2,
        )

        # Mock PneumaticToken.data
        with pytest.MonkeyPatch().context() as m:
            m.setattr(
                'src.shared_kernel.middleware.'
                'auth_middleware.PneumaticToken.data',
                AsyncMock(return_value={'user_id': 1, 'account_id': 2}),
            )

            # Act
            result = await middleware.authenticate_token(token)

            # Assert
            assert result is not None
            assert result.user_id == 1
            assert result.account_id == 2

    @pytest.mark.asyncio
    async def test_authenticate_token__invalid_token__return_none(
        self,
        middleware,
    ):
        """Test failed token authentication"""
        # Arrange
        token = 'invalid-token'

        # Mock PneumaticToken.data to return None
        with pytest.MonkeyPatch().context() as m:
            m.setattr(
                'src.shared_kernel.middleware.auth_middleware'
                '.PneumaticToken.data',
                AsyncMock(return_value=None),
            )

            # Act
            result = await middleware.authenticate_token(token)

            # Assert
            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_token__exception_occurred__return_none(
        self,
        middleware,
    ):
        """Test authentication with exception"""
        # Arrange
        token = 'error-token'

        # Mock PneumaticToken.data to raise exception
        with pytest.MonkeyPatch().context() as m:
            m.setattr(
                'src.shared_kernel.middleware.auth_middleware'
                '.PneumaticToken.data',
                AsyncMock(side_effect=Exception('Token error')),
            )

            # Act
            result = await middleware.authenticate_token(token)

            # Assert
            assert result is None

    @pytest.mark.asyncio
    async def test_dispatch__valid_token__return_success_response(
        self,
        middleware,
        mock_request,
        mock_call_next,
    ):
        """Test dispatch with valid token"""
        # Arrange
        mock_request.headers = {'Authorization': 'Bearer valid-token'}

        with pytest.MonkeyPatch().context() as m:
            m.setattr(
                'src.shared_kernel.middleware'
                '.auth_middleware.PneumaticToken.data',
                AsyncMock(return_value={'user_id': 1, 'account_id': 2}),
            )

            # Act
            response = await middleware.dispatch(mock_request, mock_call_next)

            # Assert
            assert response.status_code == 200
            assert mock_request.state.user.user_id == 1
            assert mock_request.state.user.account_id == 2

    @pytest.mark.asyncio
    async def test_dispatch__session_token__return_success_response(
        self,
        middleware,
        mock_request,
        mock_call_next,
    ):
        """Test dispatch with session token"""
        # Arrange
        mock_request.headers = {}
        mock_request.cookies = {'token': 'session-token'}

        with pytest.MonkeyPatch().context() as m:
            m.setattr(
                'src.shared_kernel.middleware.auth_middleware'
                '.PneumaticToken.data',
                AsyncMock(return_value={'user_id': 3, 'account_id': 4}),
            )

            # Act
            response = await middleware.dispatch(mock_request, mock_call_next)

            # Assert
            assert response.status_code == 200
            assert mock_request.state.user.user_id == 3
            assert mock_request.state.user.account_id == 4

    @pytest.mark.asyncio
    async def test_dispatch__no_auth_required__return_anonymous_user(
        self,
        middleware_no_auth,
        mock_request,
        mock_call_next,
    ):
        """Test dispatch without required authentication"""
        # Arrange
        mock_request.headers = {}
        mock_request.cookies = {}

        # Act
        response = await middleware_no_auth.dispatch(
            mock_request,
            mock_call_next,
        )

        # Assert
        assert response.status_code == 200
        assert mock_request.state.user.is_anonymous is True

    @pytest.mark.asyncio
    async def test_dispatch__auth_required_no_token__return_401(
        self,
        middleware,
        mock_request,
        mock_call_next,
    ):
        """Test dispatch with required auth but no token"""
        # Arrange
        mock_request.headers = {}
        mock_request.cookies = {}

        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            await middleware.dispatch(mock_request, mock_call_next)

        assert exc_info.value.error_code.code == 'AUTH_001'
