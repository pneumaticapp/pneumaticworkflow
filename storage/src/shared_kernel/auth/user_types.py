"""User types enum."""

from enum import Enum


class UserType(str, Enum):
    """User authentication types."""

    AUTHENTICATED = 'authenticated'  # Regular authorized user
    ANONYMOUS = 'anonymous'  # Anonymous user
    PUBLIC_TOKEN = 'public_token'  # Public token  # noqa: S105
    GUEST_TOKEN = 'guest_token'  # Guest token  # noqa: S105
