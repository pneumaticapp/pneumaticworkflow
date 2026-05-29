"""Tests for permission classes."""

from unittest.mock import MagicMock

import pytest
from starlette.requests import Request

from src.shared_kernel.auth.user_types import UserType
from src.shared_kernel.exceptions import PermissionDeniedError
from src.shared_kernel.permissions import (
    CombinedPermissions,
    DenyPublicToken,
    IsAuthenticated,
    check_permissions,
)


def _make_request(user=None, *, has_user: bool = True) -> MagicMock:
    """Create a mock request with optional user."""
    request = MagicMock(spec=Request)
    if has_user and user is not None:
        request.state.user = user
    elif not has_user:
        # Simulate missing user attribute
        del request.state.user
        request.state = MagicMock(spec=[])
    else:
        request.state.user = None
    return request


def _make_user(
    auth_type: str = UserType.AUTHENTICATED,
    is_anonymous: bool = False,
) -> MagicMock:
    """Create a mock user."""
    user = MagicMock()
    user.auth_type = auth_type
    user.is_anonymous = is_anonymous
    return user


class TestIsAuthenticated:
    """Test IsAuthenticated permission."""

    @pytest.mark.asyncio
    async def test_has_permission__authed_user__true(self):
        """Authenticated user passes."""
        # arrange
        user = _make_user()
        request = _make_request(user)

        # act
        result = await IsAuthenticated().has_permission(request)

        # assert
        assert result is True

    @pytest.mark.asyncio
    async def test_has_permission__anonymous__false(self):
        """Anonymous user is denied."""
        # arrange
        user = _make_user(is_anonymous=True)
        request = _make_request(user)

        # act
        result = await IsAuthenticated().has_permission(request)

        # assert
        assert result is False

    @pytest.mark.asyncio
    async def test_has_permission__no_user__false(self):
        """No user on request is denied."""
        # arrange
        request = _make_request(has_user=False)

        # act
        result = await IsAuthenticated().has_permission(request)

        # assert
        assert result is False

    @pytest.mark.asyncio
    async def test_has_permission__user_none__false(self):
        """User is None is denied."""
        # arrange
        request = _make_request(user=None)

        # act
        result = await IsAuthenticated().has_permission(request)

        # assert
        assert result is False

    @pytest.mark.asyncio
    async def test_call__denied__raise_error(self):
        """Denied user raises PermissionDeniedError."""
        # arrange
        request = _make_request(has_user=False)

        # act & assert
        with pytest.raises(PermissionDeniedError):
            await IsAuthenticated()(request)


class TestDenyPublicToken:
    """Test DenyPublicToken permission."""

    @pytest.mark.asyncio
    async def test_has_permission__session_token__true(self):
        """Session token user is allowed."""
        # arrange
        user = _make_user(auth_type=UserType.AUTHENTICATED)
        request = _make_request(user)

        # act
        result = await DenyPublicToken().has_permission(request)

        # assert
        assert result is True

    @pytest.mark.asyncio
    async def test_has_permission__public_token__false(self):
        """Public token user is denied."""
        # arrange
        user = _make_user(auth_type=UserType.PUBLIC_TOKEN)
        request = _make_request(user)

        # act
        result = await DenyPublicToken().has_permission(request)

        # assert
        assert result is False

    @pytest.mark.asyncio
    async def test_has_permission__user_none__false(self):
        """User is None → deny (safe default)."""
        # arrange
        request = _make_request(user=None)

        # act
        result = await DenyPublicToken().has_permission(request)

        # assert
        assert result is False

    @pytest.mark.asyncio
    async def test_has_permission__no_user_attr__false(self):
        """No user attribute on request → deny."""
        # arrange
        request = _make_request(has_user=False)

        # act
        result = await DenyPublicToken().has_permission(request)

        # assert
        assert result is False

    @pytest.mark.asyncio
    async def test_call__public_token__raise_error(self):
        """Public token raises PermissionDeniedError."""
        # arrange
        user = _make_user(auth_type=UserType.PUBLIC_TOKEN)
        request = _make_request(user)

        # act & assert
        with pytest.raises(PermissionDeniedError):
            await DenyPublicToken()(request)

    @pytest.mark.asyncio
    async def test_call__session_token__return_true(self):
        """Session token user returns True."""
        # arrange
        user = _make_user(auth_type=UserType.AUTHENTICATED)
        request = _make_request(user)

        # act
        result = await DenyPublicToken()(request)

        # assert
        assert result is True

    @pytest.mark.asyncio
    async def test_has_permission__guest_token__true(self):
        """Guest token user is allowed (not public)."""
        # arrange
        user = _make_user(auth_type=UserType.GUEST_TOKEN)
        request = _make_request(user)

        # act
        result = await DenyPublicToken().has_permission(request)

        # assert
        assert result is True

    @pytest.mark.asyncio
    async def test_has_permission__anonymous__true(self):
        """Anonymous user is allowed (anonymous != public)."""
        # arrange
        user = _make_user(
            auth_type=UserType.AUTHENTICATED,
            is_anonymous=True,
        )
        request = _make_request(user)

        # act
        result = await DenyPublicToken().has_permission(request)

        # assert — anonymous is NOT public token
        assert result is True


class TestCombinedPermissions:
    """Test CombinedPermissions."""

    @pytest.mark.asyncio
    async def test_combined__all_pass__true(self):
        """All permissions pass → True."""
        # arrange
        user = _make_user(auth_type=UserType.AUTHENTICATED)
        request = _make_request(user)
        combined = CombinedPermissions([
            IsAuthenticated(),
            DenyPublicToken(),
        ])

        # act
        result = await combined.has_permission(request)

        # assert
        assert result is True

    @pytest.mark.asyncio
    async def test_combined__one_fails__false(self):
        """One permission fails → False."""
        # arrange
        user = _make_user(auth_type=UserType.PUBLIC_TOKEN)
        request = _make_request(user)
        combined = CombinedPermissions([
            IsAuthenticated(),
            DenyPublicToken(),
        ])

        # act
        result = await combined.has_permission(request)

        # assert — IsAuthenticated passes but DenyPublicToken fails
        assert result is False

    @pytest.mark.asyncio
    async def test_combined__call__denied__raise_error(self):
        """Combined denial raises PermissionDeniedError."""
        # arrange
        request = _make_request(has_user=False)
        combined = CombinedPermissions([
            IsAuthenticated(),
        ])

        # act & assert
        with pytest.raises(PermissionDeniedError):
            await combined(request)

    @pytest.mark.asyncio
    async def test_combined__empty_list__true(self):
        """Empty permissions list → True (vacuous truth)."""
        # arrange
        request = _make_request(has_user=False)
        combined = CombinedPermissions([])

        # act
        result = await combined.has_permission(request)

        # assert
        assert result is True


class TestCheckPermissions:
    """Test check_permissions utility."""

    @pytest.mark.asyncio
    async def test_check__all_pass__no_error(self):
        """All permissions pass → no error."""
        # arrange
        user = _make_user(auth_type=UserType.AUTHENTICATED)
        request = _make_request(user)

        # act & assert — no error
        await check_permissions(request, [
            IsAuthenticated(),
            DenyPublicToken(),
        ])

    @pytest.mark.asyncio
    async def test_check__one_fails__raise_error(self):
        """One permission fails → PermissionDeniedError."""
        # arrange
        user = _make_user(auth_type=UserType.PUBLIC_TOKEN)
        request = _make_request(user)

        # act & assert
        with pytest.raises(PermissionDeniedError):
            await check_permissions(request, [
                IsAuthenticated(),
                DenyPublicToken(),
            ])
