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


@pytest.fixture
def make_perm_request():
    """Factory for mock requests with optional user."""

    def _factory(user=None, *, has_user: bool = True):
        request = MagicMock(spec=Request)
        if has_user and user is not None:
            request.state.user = user
        elif not has_user:
            del request.state.user
            request.state = MagicMock(spec=[])
        else:
            request.state.user = None
        return request

    return _factory


@pytest.fixture
def make_perm_user():
    """Factory for mock users."""

    def _factory(
        auth_type: str = UserType.AUTHENTICATED,
        is_anonymous: bool = False,
    ):
        user = MagicMock()
        user.auth_type = auth_type
        user.is_anonymous = is_anonymous
        return user

    return _factory


# --- IsAuthenticated ---


@pytest.mark.asyncio
async def test_is_authenticated__authed_user__true(
    make_perm_user,
    make_perm_request,
):

    # arrange
    user = make_perm_user()
    request = make_perm_request(user)

    # act
    result = await IsAuthenticated().has_permission(request)

    # assert
    assert result is True


@pytest.mark.asyncio
async def test_is_authenticated__anonymous__false(
    make_perm_user,
    make_perm_request,
):

    # arrange
    user = make_perm_user(is_anonymous=True)
    request = make_perm_request(user)

    # act
    result = await IsAuthenticated().has_permission(request)

    # assert
    assert result is False


@pytest.mark.asyncio
async def test_is_authenticated__no_user__false(
    make_perm_request,
):

    # arrange
    request = make_perm_request(has_user=False)

    # act
    result = await IsAuthenticated().has_permission(request)

    # assert
    assert result is False


@pytest.mark.asyncio
async def test_is_authenticated__user_none__false(
    make_perm_request,
):

    # arrange
    request = make_perm_request(user=None)

    # act
    result = await IsAuthenticated().has_permission(request)

    # assert
    assert result is False


@pytest.mark.asyncio
async def test_is_authenticated__denied__raise_error(
    make_perm_request,
):

    # arrange
    request = make_perm_request(has_user=False)

    # act
    with pytest.raises(PermissionDeniedError):

        # assert
        await IsAuthenticated()(request)


# --- DenyPublicToken ---


@pytest.mark.asyncio
async def test_deny_public__session_token__true(
    make_perm_user,
    make_perm_request,
):

    # arrange
    user = make_perm_user(auth_type=UserType.AUTHENTICATED)
    request = make_perm_request(user)

    # act
    result = await DenyPublicToken().has_permission(request)

    # assert
    assert result is True


@pytest.mark.asyncio
async def test_deny_public__public_token__false(
    make_perm_user,
    make_perm_request,
):

    # arrange
    user = make_perm_user(auth_type=UserType.PUBLIC_TOKEN)
    request = make_perm_request(user)

    # act
    result = await DenyPublicToken().has_permission(request)

    # assert
    assert result is False


@pytest.mark.asyncio
async def test_deny_public__user_none__false(
    make_perm_request,
):

    # arrange
    request = make_perm_request(user=None)

    # act
    result = await DenyPublicToken().has_permission(request)

    # assert
    assert result is False


@pytest.mark.asyncio
async def test_deny_public__no_user_attr__false(
    make_perm_request,
):

    # arrange
    request = make_perm_request(has_user=False)

    # act
    result = await DenyPublicToken().has_permission(request)

    # assert
    assert result is False


@pytest.mark.asyncio
async def test_deny_public__call_public__raise_error(
    make_perm_user,
    make_perm_request,
):

    # arrange
    user = make_perm_user(auth_type=UserType.PUBLIC_TOKEN)
    request = make_perm_request(user)

    # act
    with pytest.raises(PermissionDeniedError):

        # assert
        await DenyPublicToken()(request)


@pytest.mark.asyncio
async def test_deny_public__call_session__return_true(
    make_perm_user,
    make_perm_request,
):

    # arrange
    user = make_perm_user(auth_type=UserType.AUTHENTICATED)
    request = make_perm_request(user)

    # act
    result = await DenyPublicToken()(request)

    # assert
    assert result is True


@pytest.mark.asyncio
async def test_deny_public__guest_token__true(
    make_perm_user,
    make_perm_request,
):

    # arrange
    user = make_perm_user(auth_type=UserType.GUEST_TOKEN)
    request = make_perm_request(user)

    # act
    result = await DenyPublicToken().has_permission(request)

    # assert
    assert result is True


@pytest.mark.asyncio
async def test_deny_public__anonymous__true(
    make_perm_user,
    make_perm_request,
):

    # arrange
    user = make_perm_user(
        auth_type=UserType.AUTHENTICATED,
        is_anonymous=True,
    )
    request = make_perm_request(user)

    # act
    result = await DenyPublicToken().has_permission(request)

    # assert — anonymous is NOT public token
    assert result is True


# --- CombinedPermissions ---


@pytest.mark.asyncio
async def test_combined__all_pass__true(
    make_perm_user,
    make_perm_request,
):

    # arrange
    user = make_perm_user(auth_type=UserType.AUTHENTICATED)
    request = make_perm_request(user)
    combined = CombinedPermissions([
        IsAuthenticated(),
        DenyPublicToken(),
    ])

    # act
    result = await combined.has_permission(request)

    # assert
    assert result is True


@pytest.mark.asyncio
async def test_combined__one_fails__false(
    make_perm_user,
    make_perm_request,
):

    # arrange
    user = make_perm_user(auth_type=UserType.PUBLIC_TOKEN)
    request = make_perm_request(user)
    combined = CombinedPermissions([
        IsAuthenticated(),
        DenyPublicToken(),
    ])

    # act
    result = await combined.has_permission(request)

    # assert
    assert result is False


@pytest.mark.asyncio
async def test_combined__denied__raise_error(
    make_perm_request,
):

    # arrange
    request = make_perm_request(has_user=False)
    combined = CombinedPermissions([IsAuthenticated()])

    # act
    with pytest.raises(PermissionDeniedError):

        # assert
        await combined(request)


@pytest.mark.asyncio
async def test_combined__empty_list__true(
    make_perm_request,
):

    # arrange
    request = make_perm_request(has_user=False)
    combined = CombinedPermissions([])

    # act
    result = await combined.has_permission(request)

    # assert
    assert result is True


# --- check_permissions utility ---


@pytest.mark.asyncio
async def test_check_perms__all_pass__no_error(
    make_perm_user,
    make_perm_request,
):

    # arrange
    user = make_perm_user(auth_type=UserType.AUTHENTICATED)
    request = make_perm_request(user)

    # act — no error
    await check_permissions(request, [
        IsAuthenticated(),
        DenyPublicToken(),
    ])


@pytest.mark.asyncio
async def test_check_perms__one_fails__raise_error(
    make_perm_user,
    make_perm_request,
):

    # arrange
    user = make_perm_user(auth_type=UserType.PUBLIC_TOKEN)
    request = make_perm_request(user)

    # act
    with pytest.raises(PermissionDeniedError):

        # assert
        await check_permissions(request, [
            IsAuthenticated(),
            DenyPublicToken(),
        ])
