"""Authentication middleware."""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from fastapi import FastAPI

from src.shared_kernel.auth import (
    PneumaticToken,
    PublicAuthService,
)
from src.shared_kernel.auth.guest_token import GuestToken
from src.shared_kernel.auth.user_types import UserType
from src.shared_kernel.exceptions import AuthenticationError


class AuthUser:
    """Unified user class."""

    def __init__(
        self,
        auth_type: UserType,
        user_id: int | None = None,
        account_id: int | None = None,
        token: str | None = None,
    ) -> None:
        """Initialize authenticated user.

        Args:
            auth_type: Type of authentication.
            user_id: Optional user ID.
            account_id: Optional account ID.
            token: Optional authentication token.

        """
        self.auth_type = auth_type
        self.user_id = user_id
        self.account_id = account_id
        self.token = token

    @property
    def is_anonymous(self) -> bool:
        """Check if user is anonymous."""
        return self.auth_type == UserType.ANONYMOUS

    @property
    def is_public_token(self) -> bool:
        """Check if user has public token."""
        return self.auth_type == UserType.PUBLIC_TOKEN

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.auth_type == UserType.AUTHENTICATED

    @property
    def is_guest_token(self) -> bool:
        """Check if user has guest token."""
        return self.auth_type == UserType.GUEST_TOKEN


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for token and session auth.

    Adds to request:
    - request.user: AuthUser
    """

    def __init__(self, app: 'FastAPI', *, require_auth: bool = True) -> None:
        """Initialize authentication middleware.

        Args:
            app: FastAPI application instance.
            require_auth: Whether authentication is required.

        """
        super().__init__(app)
        self.security = HTTPBearer(auto_error=False)
        self.require_auth = require_auth

        self.auth_strategies = [
            ('token', 'cookie', self.authenticate_token),
            ('guest-token', 'cookie', self.authenticate_guest_token),
            ('public-token', 'cookie', self.authenticate_public_token),
            ('Authorization', 'bearer', self.authenticate_token),
            ('X-Guest-Authorization', 'header', self.authenticate_guest_token),
            (
                'X-Public-Authorization',
                'header',
                self.authenticate_public_token,
            ),
        ]

    async def authenticate_token(self, token: str) -> AuthUser | None:
        """Authenticate using token."""
        try:
            token_data = await PneumaticToken.data(token)
            if token_data:
                return AuthUser(
                    auth_type=UserType.AUTHENTICATED,
                    user_id=token_data['user_id'],
                    account_id=token_data['account_id'],
                    token=token,
                )
        except (ValueError, KeyError, TypeError):
            # Handle specific authentication errors
            pass
        return None

    async def authenticate_guest_token(self, token: str) -> AuthUser | None:
        """Authenticate guest token."""
        try:
            # This would need a function to get user data from Django
            # For now, we'll return None and implement later
            guest_token = GuestToken(token=token)
            if guest_token.payload:
                return AuthUser(
                    auth_type=UserType.GUEST_TOKEN,
                    user_id=int(guest_token['user_id'])
                    if guest_token['user_id']
                    else None,
                    account_id=int(guest_token['account_id'])
                    if guest_token['account_id']
                    else None,
                    token=token,
                )
        except (ValueError, KeyError, TypeError):
            # Handle specific guest token errors
            pass
        return None

    async def authenticate_public_token(
        self,
        raw_token: str,
    ) -> AuthUser | None:
        """Authenticate public token."""
        try:
            token = PublicAuthService.get_token(raw_token)
            if token:
                auth_data = await PublicAuthService.authenticate_public_token(
                    token,
                )
                if auth_data and 'account_id' in auth_data:
                    return AuthUser(
                        auth_type=UserType.PUBLIC_TOKEN,
                        user_id=None,
                        account_id=auth_data['account_id'],
                        token=str(token),
                    )
        except (ValueError, KeyError, TypeError):
            # Handle specific public token errors
            pass
        return None

    async def try_authenticate(self, request: Request) -> AuthUser | None:
        """Try to authenticate user using all available strategies."""
        for key, source, auth_func in self.auth_strategies:
            token = None
            if source == 'cookie':
                token = request.cookies.get(key)
            elif source == 'header':
                token = request.headers.get(key)
            elif source == 'bearer':
                authorization = await self.security(request)
                token = authorization.credentials if authorization else None

            if token:
                user = await auth_func(token)
                if user:
                    return user
        return None

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request with token or session authentication."""
        try:
            request.state.user = AuthUser(auth_type=UserType.ANONYMOUS)

            user = await self.try_authenticate(request)
            if user:
                request.state.user = user

            # If authentication is required and user is anonymous
            if self.require_auth and request.state.user.is_anonymous:
                raise AuthenticationError  # noqa: TRY301

            return await call_next(request)
        except AuthenticationError as exc:
            # Convert exception to HTTP response using existing logic
            error_response = exc.to_response(
                timestamp=datetime.now(tz=UTC).isoformat(),
                request_id=getattr(request.state, 'request_id', None),
            )
            return JSONResponse(
                status_code=exc.http_status,
                content=error_response.to_dict(),
            )
