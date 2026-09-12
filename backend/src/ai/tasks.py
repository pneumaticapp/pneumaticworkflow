from celery import shared_task
from typing import List, Tuple
from django.db.models import Exists, OuterRef

from src.celery_app import periodic_lock

from src.ai.enums import AIAgentActionType
from src.ai.models import AIAgentAction
from src.processes.enums import (
    TaskStatus,
    WorkflowStatus,
)
from src.processes.models.workflows.task import TaskPerformer


def claim_new_ai_tasks() -> List[Tuple[int, int]]:
    already_claimed = AIAgentAction.objects.filter(
        task_id=OuterRef('task_id'),
        agent__user_id=OuterRef('user_id'),
        action=AIAgentActionType.TASK_IN_PROGRESS,
        date_created__gte=OuterRef('task__date_started'),
    )
    performers = (
        TaskPerformer.objects
        .type_user()
        .not_completed()
        .exclude_directly_deleted()
        .filter(
            user__is_ai=True,
            user__ai_agent__is_active=True,
            task__status=TaskStatus.ACTIVE,
            task__workflow__status=WorkflowStatus.RUNNING,
        )
        .annotate(_already_claimed=Exists(already_claimed))
        .filter(_already_claimed=False)
        .select_related('task', 'user__ai_agent')
    )
    claimed = []
    for performer in performers:
        agent = performer.user.ai_agent
        AIAgentAction.objects.create(
            agent=agent,
            task=performer.task,
            action=AIAgentActionType.TASK_IN_PROGRESS,
        )
        claimed.append((performer.task_id, agent.id))
    return claimed


@shared_task(ignore_result=True)
def execute_ai_agent_task(task_id: int, agent_id: int) -> None:
    """Read the task description and execute it. Implementation later."""
    return


@shared_task(ignore_result=True)
def dispatch_ai_agent_tasks() -> None:

    """ Root AI Agent dispatcher """

    with periodic_lock('dispatch_ai_agent_tasks') as acquired:
        if not acquired:
            return
        claimed = claim_new_ai_tasks()
        for task_id, agent_id in claimed:
            execute_ai_agent_task.delay(task_id=task_id, agent_id=agent_id)
