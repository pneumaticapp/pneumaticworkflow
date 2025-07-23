from pneumatic_backend.generics.throttling import (
    TokenThrottle
)


class TaskPerformerGuestThrottle(TokenThrottle):
    scope = '02_processes__create_guest_performer'


class AiTemplateGenThrottle(TokenThrottle):

    skip_for_paid_accounts = False

    scope = '03_processes__template_ai_generation'
