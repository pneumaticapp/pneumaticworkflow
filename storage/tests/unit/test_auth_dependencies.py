"""Tests for the authenticated user of the endpoints."""

from src.shared_kernel.auth.dependencies import AuthenticatedUser
from src.shared_kernel.auth.user_types import ActorType, UserType
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
