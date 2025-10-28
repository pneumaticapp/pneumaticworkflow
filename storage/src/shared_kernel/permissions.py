"""Permission classes."""

from abc import ABC, abstractmethod

from fastapi import Request

from src.shared_kernel.auth.user_types import UserType
from src.shared_kernel.exceptions import (
    PermissionDeniedError,
)


class BasePermission(ABC):
    """Base permission class."""

    @abstractmethod
    async def has_permission(self, request: Request) -> bool:
        """Check if request has permission."""

    def get_error_message(self) -> str:
        """Get error message."""
        return 'Permission denied'

    async def __call__(self, request: Request) -> bool:
        """Make permission callable for use with Depends."""
        if not await self.has_permission(request):
            raise PermissionDeniedError(details=self.get_error_message())
        return True

    async def check_permission(self, request: Request) -> None:
        """Check permission and raise exception on denial."""
        await self(request)


class IsAuthenticated(BasePermission):
    """Requires authenticated user (not anonymous)."""

    async def has_permission(self, request: Request) -> bool:
        """Check if user is authenticated."""
        user = getattr(request.state, 'user', None)
        return user is not None and not user.is_anonymous

    def get_error_message(self) -> str:
        """Get authentication required error message."""
        return 'Authentication required'


class DenyPublicToken(BasePermission):
    """Denies access for users with public token."""

    async def has_permission(self, request: Request) -> bool:
        """Check if user is not using public token."""
        user = getattr(request.state, 'user', None)
        if user is None:
            return True
        # Deny if user is authenticated via public token
        return user.auth_type != UserType.PUBLIC_TOKEN

    def get_error_message(self) -> str:
        """Get public token access denied error message."""
        return 'Access denied for public tokens'


async def check_permissions(
    request: Request,
    permissions: list[BasePermission],
) -> None:
    """Check all permissions for request."""
    for permission in permissions:
        await permission.check_permission(request)


# Permission instances
_is_authenticated = IsAuthenticated()
_deny_public_token = DenyPublicToken()


# FastAPI dependency wrappers
async def is_authenticated(request: Request) -> bool:
    """FastAPI dependency for authentication check."""
    return await _is_authenticated(request)


async def deny_public_token(request: Request) -> bool:
    """FastAPI dependency for public token denial."""
    return await _deny_public_token(request)


# Combined permissions class
class CombinedPermissions(BasePermission):
    """Combines multiple permissions."""

    def __init__(self, permissions: list[BasePermission]) -> None:
        """Initialize combined permissions.

        Args:
            permissions: List of permissions to combine.

        """
        self.permissions = permissions

    async def has_permission(self, request: Request) -> bool:
        """Check all permissions."""
        for permission in self.permissions:
            if not await permission.has_permission(request):
                return False
        return True

    def get_error_message(self) -> str:
        """Get access denied error message."""
        return 'Access denied'


# Predefined permission combinations
_authenticated_no_public = CombinedPermissions(
    [
        IsAuthenticated(),
        DenyPublicToken(),
    ],
)


# FastAPI dependency wrapper for combined permissions
async def authenticated_no_public(request: Request) -> bool:
    """FastAPI dependency for authenticated users without public tokens."""
    return await _authenticated_no_public(request)
