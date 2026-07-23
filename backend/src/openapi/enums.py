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
    ACCOUNTS_INVITES = '/accounts/invites'
    ACCOUNTS_DIGEST_UNSUB = '/accounts/digest'
    ACCOUNTS_EMAILS_UNSUB = '/accounts/emails'
    ACCOUNTS_NOTIFICATIONS_READ = '/accounts/notifications/read'
    ACCOUNTS_PUBLIC = '/accounts/public'
    AUTH_SIGNUP = '/auth/signup'
    AUTH_SIGNOUT = '/auth/signout'
    AUTH_VERIFICATION = '/auth/verification'
    AUTH_RESEND_VERIFICATION = '/auth/resend-verification'
    AUTH_CHANGE_PASSWORD = '/auth/change-password'
    AUTH_SUPERUSER_TOKEN = '/auth/superuser/token'
    AUTH_AUTH0 = '/auth/auth0'
    AUTH_OKTA = '/auth/okta'
    AUTH_OKTA_LOGOUT = '/auth/okta-logout'
    AUTH_TOKEN_OBTAIN = '/auth/token/obtain'
    AUTH_GOOGLE = '/auth/google'
    AUTH_MICROSOFT = '/auth/microsoft'
    PAYMENT = '/payment'
    APPLICATIONS = '/applications'

    # Internal / CMS — no value for API integrators.
    FAQ = '/faq'
    PAGES = '/pages'
    NAVIGATION = '/navigation'
    SERVICES = '/services'
    NOTIFICATIONS = '/notifications'

    ALL = (
        WEBHOOKS_BUFFER,
        ACCOUNTS_API_KEY,
        ACCOUNTS_INVITES_TOKEN,
        ACCOUNTS_INVITES,
        ACCOUNTS_DIGEST_UNSUB,
        ACCOUNTS_EMAILS_UNSUB,
        ACCOUNTS_NOTIFICATIONS_READ,
        ACCOUNTS_PUBLIC,
        AUTH_SIGNUP,
        AUTH_SIGNOUT,
        AUTH_VERIFICATION,
        AUTH_RESEND_VERIFICATION,
        AUTH_CHANGE_PASSWORD,
        AUTH_SUPERUSER_TOKEN,
        AUTH_TOKEN_OBTAIN,
        AUTH_AUTH0,
        AUTH_OKTA,
        AUTH_OKTA_LOGOUT,
        AUTH_GOOGLE,
        AUTH_MICROSOFT,
        PAYMENT,
        APPLICATIONS,
        FAQ,
        PAGES,
        NAVIGATION,
        SERVICES,
        NOTIFICATIONS,
    )
