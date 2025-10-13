"""Authentication middleware"""

from typing import Any, Awaitable, Callable, Optional

from fastapi import Request, Response
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from src.shared_kernel.auth import (
    PneumaticToken,
    PublicAuthService,
)
from src.shared_kernel.auth.guest_token import GuestToken
from src.shared_kernel.auth.user_types import UserType
from src.shared_kernel.exceptions import AuthenticationError


class AuthUser:
    """Unified user class"""

    def __init__(
        self,
        auth_type: UserType,
        user_id: Optional[int] = None,
        account_id: Optional[int] = None,
        token: Optional[str] = None,
    ) -> None:
        self.auth_type = auth_type
        self.user_id = user_id
        self.account_id = account_id
        self.token = token

    @property
    def is_anonymous(self) -> bool:
        return self.auth_type == UserType.ANONYMOUS

    @property
    def is_public_token(self) -> bool:
        return self.auth_type == UserType.PUBLIC_TOKEN

    @property
    def is_authenticated(self) -> bool:
        return self.auth_type == UserType.AUTHENTICATED

    @property
    def is_guest_token(self) -> bool:
        return self.auth_type == UserType.GUEST_TOKEN


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for token and session auth

    Adds to request:
    - request.user: AuthUser
    """

    def __init__(self, app: Any, require_auth: bool = True) -> None:
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

    async def authenticate_token(self, token: str) -> Optional[AuthUser]:
        """Authenticate using token"""
        try:
            token_data = await PneumaticToken.data(token)
            if token_data:
                return AuthUser(
                    auth_type=UserType.AUTHENTICATED,
                    user_id=token_data['user_id'],
                    account_id=token_data['account_id'],
                    token=token,
                )
            return None
        except Exception:
            return None

    async def authenticate_guest_token(self, token: str) -> Optional[AuthUser]:
        """Authenticate guest token"""
        try:
            # This would need a function to get user data from Django
            # For now, we'll return None and implement later
            guest_token = GuestToken(token=token)
            if guest_token.payload:
                return AuthUser(
                    auth_type=UserType.GUEST_TOKEN,
                    user_id=guest_token['user_id'],
                    account_id=guest_token['account_id'],
                    token=token,
                )
            return None
        except Exception:
            return None

    async def authenticate_public_token(
        self, raw_token: str
    ) -> Optional[AuthUser]:
        """Authenticate public token"""
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
            return None
        except Exception:
            return None

    async def try_authenticate(self, request: Request) -> Optional[AuthUser]:
        """Try to authenticate user using all available strategies"""
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
        """Process request with token or session authentication"""
        request.state.user = AuthUser(auth_type=UserType.ANONYMOUS)

        user = await self.try_authenticate(request)
        if user:
            request.state.user = user

        # If authentication is required and user is anonymous
        if self.require_auth and request.state.user.is_anonymous:
            raise AuthenticationError()

        return await call_next(request)
