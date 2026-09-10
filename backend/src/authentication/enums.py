from typing_extensions import Literal, TypedDict


class SSOProvider:

    AUTH0 = 'auth0'
    OKTA = 'okta'

    CHOICES = (
        (AUTH0, 'Auth0'),
        (OKTA, 'Okta'),
    )

    LITERALS = Literal[
        AUTH0,
        OKTA,
    ]


class GuestCachedStatus:

    ACTIVE = 1
    INACTIVE = 0


class ResetPasswordStatus:

    VALID = 0
    EXPIRED = 1
    INVALID = 2

    CHOICES = (
        (VALID, 'Valid'),
        (EXPIRED, 'Expired'),
        (INVALID, 'Invalid'),
    )


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


class LoginFailedReason:

    """ Why a sign in was refused, the reason of a user.login_failed
        event. One value per refusing branch, so that an alert can
        tell a brute force burst from a deactivated account. """

    BAD_CREDENTIALS = 'bad_credentials'
    ACCOUNT_INACTIVE = 'account_inactive'
    SSO_REQUIRED = 'sso_required'

    LITERALS = Literal[
        BAD_CREDENTIALS,
        ACCOUNT_INACTIVE,
        SSO_REQUIRED,
    ]


class OktaLogoutFormat:

    EMAIL = 'email'
    ISS_SUB = 'iss_sub'

    LITERALS = Literal[
        EMAIL,
        ISS_SUB,
    ]


class OktaIssSubData(TypedDict):
    format: OktaLogoutFormat.LITERALS
    iss: str
    sub: str


class OktaEmailSubData(TypedDict):
    format: OktaLogoutFormat.LITERALS
    email: str
