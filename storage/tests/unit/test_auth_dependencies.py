"""Tests for the authenticated user of the endpoints."""

import pytest

from src.shared_kernel.auth.dependencies import AuthenticatedUser
from src.shared_kernel.auth.user_types import (
    JournalAuthType,
    JournalUserType,
    UserType,
)
from src.shared_kernel.middleware.auth_middleware import AuthUser


def test_init__api_key_user__api_auth_carried():
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
    assert user.is_api_key is True
    assert user.journal_user_type == JournalUserType.USER
    assert user.journal_auth_type == JournalAuthType.API
    assert user.user_id == 1
    assert user.account_id == 2


def test_init__session_user__user_auth():
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
    assert user.journal_user_type == JournalUserType.USER
    assert user.journal_auth_type == JournalAuthType.USER


def test_init__public_token__no_actor_shared_auth():
    # arrange
    auth_user = AuthUser(
        auth_type=UserType.PUBLIC_TOKEN,
        account_id=2,
        token='public',
    )

    # act
    user = AuthenticatedUser(auth_user)

    # assert
    assert user.journal_user_type is None
    assert user.journal_auth_type == JournalAuthType.SHARED
    assert user.user_id is None


def test_init__embed_token__embed_carried():
    # arrange
    auth_user = AuthUser(
        auth_type=UserType.PUBLIC_TOKEN,
        account_id=2,
        token='embed',
        is_embed_token=True,
    )

    # act
    user = AuthenticatedUser(auth_user)

    # assert
    assert user.is_embed_token is True
    assert user.journal_user_type is None
    assert user.journal_auth_type == JournalAuthType.EMBEDDED


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
