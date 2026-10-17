from celery import shared_task
from django.db.models import F
from src.accounts.enums import NotificationType
from src.accounts.models import Notification
from src.ai.services.agent import AIAgentService, MAX_RUN_FAILURES
from src.celery_app import periodic_lock

from src.ai.models import AIAgent
from src.processes.models.workflows.task import TaskPerformer


@shared_task(ignore_result=True)
def complete_ai_agent_task(task_id: int, agent_id: int) -> None:

    agent = AIAgent.objects.get(id=agent_id)
    service = AIAgentService(instance=agent, user=agent.user)
    service.complete_task(task_id)


@shared_task(ignore_result=True)
def dispatch_ai_agent_new_tasks() -> None:

    """ Dispatch to AI agents the new tasks and the tasks whose
        every run failed, until the failures reach MAX_RUN_FAILURES.
        The agent is assigned directly or as a group member,
        an agent assigned both ways is dispatched once """

    with periodic_lock('dispatch_ai_agent_tasks') as acquired:
        if not acquired:
            return
        assignments = set()
        for performers in (
            TaskPerformer.objects.ai_agent_user_assignments(),
            TaskPerformer.objects.ai_agent_group_assignments(),
        ):
            assignments.update(
                performers
                .with_ai_agent_runs()
                .filter(
                    ai_agent_runs=F('ai_agent_failures'),
                    ai_agent_runs__lt=MAX_RUN_FAILURES,
                )
                .values_list('task_id', 'ai_agent_id'),
            )
        for task_id, agent_id in sorted(assignments):
            complete_ai_agent_task.delay(task_id=task_id, agent_id=agent_id)


@shared_task(ignore_result=True)
def execute_ai_agent_reply(notification_id: int, agent_id: int) -> None:

    """ Handle an AI agent mention. Implementation later.
        In answer create workflow event with mention to author
    """

    agent = AIAgent.objects.get(id=agent_id)
    service = AIAgentService(instance=agent, user=agent.user)
    service.reply_to_comment(notification_id=notification_id)


@shared_task(ignore_result=True)
def dispatch_ai_agent_new_notifications() -> None:

    """ Dispatch to AI agents the new mentions and the mentions whose
        every run failed, until the failures reach MAX_RUN_FAILURES """

    with periodic_lock('dispatch_ai_agent_new_notifications') as acquired:
        if not acquired:
            return
        notifications = (
            Notification.objects
            .filter(
                type=NotificationType.MENTION,
                user__is_ai=True,
                user__ai_agent__is_active=True,
            )
            .with_ai_agent_runs()
            .filter(
                ai_agent_runs=F('ai_agent_failures'),
                ai_agent_runs__lt=MAX_RUN_FAILURES,
            )
            .select_related('user__ai_agent')
        )
        for notification in notifications:
            agent_id = notification.user.ai_agent.id
            execute_ai_agent_reply.delay(
                notification_id=notification.id,
                agent_id=agent_id,
            )
