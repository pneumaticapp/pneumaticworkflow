from django.db.models import QuerySet

from src.ai.enums import OpenAIPromptTarget
from src.generics.querysets import AccountBaseQuerySet


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


class AIProviderQuerySet(AccountBaseQuerySet):
    pass


class AIAgentQuerySet(AccountBaseQuerySet):
    pass


class AIAgentActionQuerySet(QuerySet):

    def by_agent(self, agent_id: int):
        return self.filter(agent_id=agent_id)

    def by_task(self, task_id: int):
        return self.filter(task_id=task_id)

    def by_action(self, action: str):
        return self.filter(action=action)
