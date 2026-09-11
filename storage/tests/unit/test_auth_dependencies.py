"""Tests for the authenticated user of the endpoints."""

import pytest

from src.shared_kernel.auth.dependencies import (
    AuthenticatedUser,
    get_current_user,
)
from src.shared_kernel.auth.user_types import ActorType, UserType
from src.shared_kernel.exceptions import AuthenticationError
from src.shared_kernel.middleware.auth_middleware import AuthUser


def test_init__api_key_user__actor_carried():
    # arrange
    auth_user = AuthUser(
        auth_type=UserType.AUTHENTICATED,
        user_id=1,
        account_id=2,
        token='key',
        is_api_key=True,
    )

    # act
    user = AuthenticatedUser(auth_user)

    # assert
    assert user.actor_type == ActorType.API_KEY
    assert user.user_id == 1
    assert user.account_id == 2


def test_init__session_user__actor_user():
    # arrange
    auth_user = AuthUser(
        auth_type=UserType.AUTHENTICATED,
        user_id=1,
        account_id=2,
        token='session',
    )

    # act
    user = AuthenticatedUser(auth_user)

    # assert
    assert user.actor_type == ActorType.USER


def test_init__public_token__actor_guest_without_user():
    # arrange
    auth_user = AuthUser(
        auth_type=UserType.PUBLIC_TOKEN,
        account_id=2,
        token='public',
    )

    # act
    user = AuthenticatedUser(auth_user)

    # assert
    assert user.actor_type == ActorType.GUEST
    assert user.user_id is None


def test_init__no_account__type_error():
    """An authenticated user always belongs to an account."""

    # arrange
    auth_user = AuthUser(
        auth_type=UserType.AUTHENTICATED,
        user_id=1,
        account_id=None,
        token='session',
    )

    # act
    with pytest.raises(TypeError) as ex:
        AuthenticatedUser(auth_user)

    # assert
    assert str(ex.value) == (
        'account_id must not be None for authenticated users'
    )


async def test_get_current_user__authenticated__user_returned(mocker):
    # arrange
    request = mocker.Mock()
    request.state.user = AuthUser(
        auth_type=UserType.AUTHENTICATED,
        user_id=1,
        account_id=2,
        token='session',
    )

    # act
    user = await get_current_user(request)

    # assert
    assert user.user_id == 1
    assert user.account_id == 2


async def test_get_current_user__no_user_in_state__raise(mocker):
    # arrange
    request = mocker.Mock()
    request.state.user = None

    # act
    with pytest.raises(AuthenticationError) as ex:
        await get_current_user(request)

    # assert
    assert ex.value.details == 'User not authenticated'


async def test_get_current_user__anonymous__raise(mocker):
    # arrange
    request = mocker.Mock()
    request.state.user = AuthUser(auth_type=UserType.ANONYMOUS)

    # act
    with pytest.raises(AuthenticationError) as ex:
        await get_current_user(request)

    # assert
    assert ex.value.details == 'User not authenticated'
