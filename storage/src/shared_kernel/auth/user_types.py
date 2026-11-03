"""User types enum."""

from enum import StrEnum


class UserType(StrEnum):
    """User authentication types."""

    AUTHENTICATED = 'authenticated'  # Regular authorized user
    ANONYMOUS = 'anonymous'  # Anonymous user
    PUBLIC_TOKEN = 'public_token'  # Public token  # noqa: S105
    GUEST_TOKEN = 'guest_token'  # Guest token  # noqa: S105


class JournalUserType(StrEnum):
    """Kind of the person who acted, for the audit journal.

    The vocabulary of the backend (UserType there): a user of the
    account or a guest of one task. A request without a person, a
    public or an embed token, has no actor at all.

    Part of the event contract: file_service_contract.json in the
    backend fixtures lists these values under user_types and
    test_events_schema.py pins them here.
    """

    USER = 'user'
    GUEST = 'guest'


class JournalAuthType(StrEnum):
    """Credential behind the request, for the audit journal.

    The vocabulary of the backend (AuthTokenType there), without the
    webhook the file service never sees.

    Part of the event contract: file_service_contract.json in the
    backend fixtures lists these values under auth_types and
    test_events_schema.py pins them here.
    """

    USER = 'User'
    API = 'API'
    GUEST = 'Guest'
    SHARED = 'Shared'
    EMBEDDED = 'Embedded'
