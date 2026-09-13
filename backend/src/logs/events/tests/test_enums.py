import pytest

from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    AUTH_TYPE_ACTOR_TYPES,
    ActorType,
    actor_type_from_auth,
)


@pytest.mark.parametrize(
    ('auth_type', 'actor_type'),
    [
        (AuthTokenType.USER, ActorType.USER),
        (AuthTokenType.API, ActorType.API_KEY),
        (AuthTokenType.GUEST, ActorType.GUEST),
        (AuthTokenType.PUBLIC, ActorType.GUEST),
        (AuthTokenType.EMBEDDED, ActorType.GUEST),
        (AuthTokenType.WEBHOOK, ActorType.SYSTEM),
    ],
)
def test_actor_type_from_auth__known_token__expected_actor(
    auth_type,
    actor_type,
):

    # act
    result = actor_type_from_auth(auth_type)

    # assert
    assert result == actor_type


def test_actor_type_from_auth__no_token__system():

    """ Celery, a management command and any other call outside a
        request have no token type at all. """

    # act
    result = actor_type_from_auth(None)

    # assert
    assert result == ActorType.SYSTEM


def test_actor_type_from_auth__empty_token__system():

    # act
    result = actor_type_from_auth('')

    # assert
    assert result == ActorType.SYSTEM


def test_actor_type_from_auth__unknown_token__system():

    """ A new authentication type must not invent an actor type: an
        auditor reads "system" and looks for the source elsewhere. """

    # act
    result = actor_type_from_auth('Something')

    # assert
    assert result == ActorType.SYSTEM


def test_auth_type_actor_types__every_token_type__mapped():

    """ A new authentication type needs a line in the mapping, or its
        requests would all be reported as made by the system. """

    # arrange
    declared = set(AuthTokenType.LITERALS.__args__)

    # act
    mapped = set(AUTH_TYPE_ACTOR_TYPES)

    # assert
    assert mapped == declared
    assert AUTH_TYPE_ACTOR_TYPES[AuthTokenType.WEBHOOK] == ActorType.SYSTEM
