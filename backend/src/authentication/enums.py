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


class GrantType:
    AUTHORIZATION_CODE = 'authorization_code'
    REFRESH_TOKEN = 'refresh_token'

    ALLOWED = (AUTHORIZATION_CODE, REFRESH_TOKEN)


class TokenEndpointAuthMethod:
    NONE = 'none'
    CLIENT_SECRET_BASIC = 'client_secret_basic'

    ALLOWED = (NONE, CLIENT_SECRET_BASIC)


class OAuthErrorCode:
    INVALID_REQUEST = 'invalid_request'
    INVALID_GRANT = 'invalid_grant'
    INVALID_TARGET = 'invalid_target'
    INVALID_TOKEN = 'invalid_token'
    INVALID_CLIENT_METADATA = 'invalid_client_metadata'
    INVALID_LOGIN_CODE = 'invalid_login_code'
    ACCESS_DENIED = 'access_denied'
    INSUFFICIENT_SCOPE = 'insufficient_scope'
    TEMPORARILY_UNAVAILABLE = 'temporarily_unavailable'
    SERVICE_AUTH_FAILED = 'service_auth_failed'
