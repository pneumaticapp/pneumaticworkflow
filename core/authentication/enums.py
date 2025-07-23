from typing_extensions import Literal


class GuestCachedStatus:

    ACTIVE = 1
    INACTIVE = 0


class ResetPasswordStatus:

    VALID = 0
    EXPIRED = 1
    INVALID = 2


class AuthTokenType:

    PUBLIC = 'Shared'
    EMBEDDED = 'Embedded'
    API = 'API'
    GUEST = 'Guest'
    USER = 'User'
    WEBHOOK = 'Webhook'

    EXTERNAL_TYPES = {PUBLIC, EMBEDDED, API, WEBHOOK}
    PUBLIC_TYPES = {PUBLIC, EMBEDDED}
    LITERALS = Literal[
        PUBLIC,
        EMBEDDED,
        API,
        GUEST,
        USER,
        WEBHOOK,
    ]
