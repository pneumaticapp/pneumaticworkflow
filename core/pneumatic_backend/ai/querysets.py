from django.db.models import QuerySet
from pneumatic_backend.ai.enums import OpenAIPromptTarget


class OpenAiPromptQueryset(QuerySet):

    def active(self):
        return self.filter(is_active=True)

    def target_steps(self):
        return self.filter(target=OpenAIPromptTarget.GET_STEPS)

    def by_target(self, target: str):
        return self.filter(target=target)


class OpenAiPromptMessageQueryset(QuerySet):

    def active(self):
        return self.filter(is_active=True)
