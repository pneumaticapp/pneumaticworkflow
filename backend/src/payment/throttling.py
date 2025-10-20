from src.generics.throttling import (
    ApiKeyThrottle,
    TokenThrottle,
)


class PurchaseTokenThrottle(TokenThrottle):
    scope = '05_payment__purchase__user'


class PurchaseApiThrottle(ApiKeyThrottle):
    scope = '06_payment__purchase__api'
