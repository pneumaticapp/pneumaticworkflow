"""User types enum."""

from enum import StrEnum


class UserType(StrEnum):
    """User authentication types."""

    AUTHENTICATED = 'authenticated'  # Regular authorized user
    ANONYMOUS = 'anonymous'  # Anonymous user
    PUBLIC_TOKEN = 'public_token'  # Public token  # noqa: S105
    GUEST_TOKEN = 'guest_token'  # Guest token  # noqa: S105


class ActorType(StrEnum):
    """Who acted, in the vocabulary of the backend (ActorType there).

    Part of the event contract, checked by the backend test
    src/logs/events/tests/test_file_service_contract.py.
    """

    USER = 'user'
    API_KEY = 'api_key'
    GUEST = 'guest'
