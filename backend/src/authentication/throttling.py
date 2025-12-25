from src.generics.throttling import (
    AnonThrottle,
    CustomSimpleRateThrottle,
)


class AuthMSTokenThrottle(CustomSimpleRateThrottle):
    scope = '07_auth_ms__token'


class AuthMSAuthUriThrottle(CustomSimpleRateThrottle):
    scope = '08_auth_ms__auth_uri'


class SSOTokenThrottle(CustomSimpleRateThrottle):
    scope = '09_sso__token'


class SSOAuthUriThrottle(CustomSimpleRateThrottle):
    scope = '10_sso__auth_uri'


class AuthResetPasswordThrottle(AnonThrottle):
    scope = '11_auth__reset_password'


class AuthGoogleTokenThrottle(CustomSimpleRateThrottle):
    scope = '12_auth_google__token'


class AuthGoogleAuthUriThrottle(CustomSimpleRateThrottle):
    scope = '13_auth_google__auth_uri'
