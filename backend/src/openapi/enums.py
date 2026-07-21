"""OpenAPI schema generation constants."""


class ExcludedPath:
    """Paths excluded from the public OpenAPI schema.

    Endpoints with PrivateApiPermission / StagingPermission
    (including via get_permissions()) are filtered in
    preprocessing. Keep path prefixes here for:
    - defense in depth on known private ops;
    - endpoints intentionally hidden from the public schema.
    When adding a ViewSet action that uses get_permissions()
    with PrivateApiPermission, verify the hook covers it
    (see openapi/tests/test_preprocessing.py) or add a path.
    """

    WEBHOOKS_BUFFER = '/webhooks/buffer'
    ACCOUNTS_API_KEY = '/accounts/api-key'
    ACCOUNTS_INVITES_TOKEN = '/accounts/invites/token'
    AUTH_SIGNUP = '/auth/signup'
    AUTH_SIGNOUT = '/auth/signout'
    AUTH_VERIFICATION = '/auth/verification'
    AUTH_RESEND_VERIFICATION = '/auth/resend-verification'
    AUTH_CHANGE_PASSWORD = '/auth/change-password'
    AUTH_SUPERUSER_TOKEN = '/auth/superuser/token'

    ALL = (
        WEBHOOKS_BUFFER,
        ACCOUNTS_API_KEY,
        ACCOUNTS_INVITES_TOKEN,
        AUTH_SIGNUP,
        AUTH_SIGNOUT,
        AUTH_VERIFICATION,
        AUTH_RESEND_VERIFICATION,
        AUTH_CHANGE_PASSWORD,
        AUTH_SUPERUSER_TOKEN,
    )
