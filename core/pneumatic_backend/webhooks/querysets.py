from pneumatic_backend.generics.querysets import AccountBaseQuerySet
from pneumatic_backend.webhooks.enums import HookEvent


class WebHookQuerySet(AccountBaseQuerySet):

    def for_event(self, event_name: HookEvent):
        return self.filter(event=event_name)
