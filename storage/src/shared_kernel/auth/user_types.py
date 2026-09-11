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

    Part of the event contract: file_service_contract.json in the
    backend fixtures lists these values, test_events_schema.py pins
    them here and test_file_service_contract.py checks that the backend
    declares every one of them.
    """

    USER = 'user'
    API_KEY = 'api_key'
    GUEST = 'guest'
