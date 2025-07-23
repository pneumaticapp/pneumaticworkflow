from pneumatic_backend.generics.querysets import AccountBaseQuerySet
from pneumatic_backend.webhooks.enums import HookEvent


class WebHookQuerySet(AccountBaseQuerySet):

    def for_event(self, event_name: HookEvent):
        return self.filter(event=event_name)

    def wf_started(self):
        return self.filter(event=HookEvent.WORKFLOW_STARTED)

    def wf_completed(self):
        return self.filter(event=HookEvent.WORKFLOW_COMPLETED)

    def task_completed(self):
        return self.filter(event=HookEvent.TASK_COMPLETED)

    def task_returned(self):
        return self.filter(event=HookEvent.TASK_RETURNED)
