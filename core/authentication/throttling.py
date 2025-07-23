from pneumatic_backend.generics.throttling import (
    CustomSimpleRateThrottle,
    AnonThrottle,
)


class AuthMSTokenThrottle(CustomSimpleRateThrottle):
    scope = '07_auth_ms__token'


class AuthMSAuthUriThrottle(CustomSimpleRateThrottle):
    scope = '08_auth_ms__auth_uri'


class Auth0TokenThrottle(CustomSimpleRateThrottle):
    scope = '09_auth0__token'


class Auth0AuthUriThrottle(CustomSimpleRateThrottle):
    scope = '10_auth0__auth_uri'


class AuthResetPasswordThrottle(AnonThrottle):
    scope = '11_auth__reset_password'
