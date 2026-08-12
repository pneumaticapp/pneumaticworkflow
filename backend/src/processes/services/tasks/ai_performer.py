from django.contrib.auth import get_user_model

from src.ai.dispatch import dispatch_ai_performers
from src.ai.models import AIAgent
from src.ai.providers import ai_performers_active
from src.authentication.enums import AuthTokenType
from src.processes.enums import DirectlyStatus, PerformerType
from src.processes.messages.template import MSG_PT_0076
from src.processes.messages.workflow import (
    MSG_PW_0016,
    MSG_PW_0094,
    MSG_PW_0095,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.services.tasks.base import (
    BasePerformerService2,
)
from src.processes.services.tasks.exceptions import (
    AiPerformerServiceException,
)
from src.processes.services.workflow_action import (
    WorkflowActionService,
)

UserModel = get_user_model()


class AiPerformerService(BasePerformerService2):

    """ Runtime add/remove of AI performers on an active task.
        Adding dispatches a run immediately; removing invalidates any
        queued run (the worker re-checks the assignment on pickup) """

    def _get_agent(self, ai_agent_id: int) -> AIAgent:
        try:
            return (
                AIAgent.objects
                .on_account(self.user.account_id)
                .active()
                .get(id=ai_agent_id)
            )
        except AIAgent.DoesNotExist as ex:
            raise AiPerformerServiceException(MSG_PW_0094) from ex

    def _validate_create(self):
        if not ai_performers_active(self.task.account):
            raise AiPerformerServiceException(MSG_PT_0076)
        # an agent on a task with nothing to fill would immediately
        # complete it with an empty output
        if not self.task.output.exists():
            raise AiPerformerServiceException(MSG_PW_0095)

    def create_performer(self, ai_agent_id: int) -> None:
        self._validate()
        self._validate_create()
        agent = self._get_agent(ai_agent_id=ai_agent_id)
        task_performer, created = TaskPerformer.objects.get_or_create(
            task_id=self.task.id,
            type=PerformerType.AI,
            ai_agent_id=agent.id,
            defaults={'directly_status': DirectlyStatus.CREATED},
        )
        if task_performer.directly_status == DirectlyStatus.DELETED:
            task_performer.directly_status = DirectlyStatus.CREATED
            task_performer.save(update_fields=['directly_status'])
            created = True
        if created:
            dispatch_ai_performers(self.task)

    def delete_performer(self, ai_agent_id: int) -> None:
        self._validate()
        performers = (
            TaskPerformer.objects
            .by_task(self.task.id)
            .exclude_directly_deleted()
        )
        task_performer = performers.filter(
            type=PerformerType.AI,
            ai_agent_id=ai_agent_id,
        ).first()
        if task_performer is None:
            return
        if performers.count() == 1:
            raise AiPerformerServiceException(MSG_PW_0016)
        task_performer.directly_status = DirectlyStatus.DELETED
        task_performer.save(update_fields=['directly_status'])
        self.task.refresh_from_db()
        if self.task.can_be_completed():
            service = WorkflowActionService(
                user=self._get_completing_user(),
                workflow=self.task.workflow,
                is_superuser=False,
                auth_type=AuthTokenType.USER,
            )
            service.complete_task(task=self.task)

    def _get_completing_user(self) -> UserModel:

        """ Removing a pending AI performer can leave the task with
            every remaining performer completed; the completion is
            recorded for the first human who completed it, falling
            back to the requesting admin """

        return self.task.get_first_completed_human() or self.user
