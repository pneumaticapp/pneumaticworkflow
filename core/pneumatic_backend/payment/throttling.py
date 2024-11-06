from pneumatic_backend.generics.throttling import (
    TokenThrottle,
    ApiKeyThrottle,
)


class PurchaseTokenThrottle(TokenThrottle):
    scope = '05_payment__purchase__user'


class PurchaseApiThrottle(ApiKeyThrottle):
    scope = '06_payment__purchase__api'
