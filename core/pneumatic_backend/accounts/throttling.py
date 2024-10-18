from pneumatic_backend.generics.throttling import (
    TokenThrottle
)


class InvitesTokenThrottle(TokenThrottle):
    scope = '01_accounts_invites__token'
