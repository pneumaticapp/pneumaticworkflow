"""Authentication dependencies."""

from fastapi import Request

from src.shared_kernel.exceptions import (
    AuthenticationError,
)
from src.shared_kernel.middleware.auth_middleware import AuthUser


class AuthenticatedUser(AuthUser):
    """Authenticated user with guaranteed non-null fields.

    Built from the AuthUser the middleware put on the request, so it
    carries the same fields and properties; what it adds is the promise
    that account_id is set.
    """

    account_id: int

    def __init__(self, auth_user: AuthUser) -> None:
        """Initialize authenticated user.

        Args:
            auth_user: Base authenticated user.

        """
        if auth_user.account_id is None:
            msg = 'account_id must not be None for authenticated users'
            raise TypeError(msg)
        super().__init__(
            auth_type=auth_user.auth_type,
            user_id=auth_user.user_id,
            account_id=auth_user.account_id,
            token=auth_user.token,
            is_api_key=auth_user.is_api_key,
        )


async def get_current_user(request: Request) -> AuthenticatedUser:
    """Get current authenticated user from request state.

    Note: only be used in endpoints with authentication requirements.
    """
    user = getattr(request.state, 'user', None)

    if not user or user.is_anonymous or user.account_id is None:
        raise AuthenticationError(details='User not authenticated')

    return AuthenticatedUser(user)
