"""Authentication dependencies"""

from typing import TYPE_CHECKING

from fastapi import Request

from src.shared_kernel.auth.user_types import UserType
from src.shared_kernel.exceptions import (
    AuthenticationError,
    MissingAccountIdError,
)

if TYPE_CHECKING:
    from src.shared_kernel.middleware.auth_middleware import AuthUser


class AuthenticatedUser:
    """Authenticated user with guaranteed non-null fields"""

    def __init__(self, auth_user: 'AuthUser') -> None:
        if auth_user.is_anonymous or auth_user.account_id is None:
            raise MissingAccountIdError

        self.auth_type = auth_user.auth_type
        self.user_id = auth_user.user_id
        self.account_id: int = auth_user.account_id
        self.token = auth_user.token

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def is_public_token(self) -> bool:
        return self.auth_type == UserType.PUBLIC_TOKEN

    @property
    def is_authenticated(self) -> bool:
        return self.auth_type == UserType.AUTHENTICATED

    @property
    def is_guest_token(self) -> bool:
        return self.auth_type == UserType.GUEST_TOKEN


async def get_current_user(request: Request) -> AuthenticatedUser:
    """Get current authenticated user from request state

    Note: only be used in endpoints with authentication requirements
    """
    user = getattr(request.state, 'user', None)

    if not user or user.is_anonymous or user.account_id is None:
        raise AuthenticationError(details='User not authenticated')

    return AuthenticatedUser(user)
