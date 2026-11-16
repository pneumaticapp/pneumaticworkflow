from celery import shared_task
from django.db.models import Q
from src.accounts.enums import NotificationType
from src.accounts.models import Notification
from src.ai.models import AIAgent, AIAgentAction
from src.ai.services.agent import AIAgentService
from src.celery_app import periodic_lock
from src.processes.enums import (
    DirectlyStatus,
    TaskStatus,
)
from src.processes.models.workflows.task import Task, TaskPerformer


@shared_task(ignore_result=True)
def complete_ai_agent_task(task_id: int, agent_id: int) -> None:

    agent = AIAgent.objects.get(id=agent_id)
    service = AIAgentService(instance=agent, user=agent.user)
    service.complete_task(task_id)


@shared_task(ignore_result=True)
def dispatch_ai_agent_new_tasks() -> None:

    """ Dispatch the active tasks assigned to the active AI agents
        which the agent has not completed and which have no run
        events since the task was started. """

    with periodic_lock('dispatch_ai_agent_tasks') as acquired:
        if not acquired:
            return

        agents = (
            AIAgent.objects
            .filter(is_active=True)
            .order_by('id')
            .only('id', 'user_id')
        )
        for agent in agents:
            performers = TaskPerformer.objects.exclude(
                directly_status=DirectlyStatus.DELETED,
            )
            task_ids = (
                performers
                .filter(
                    Q(user_id=agent.user_id) | Q(
                        group__users__id=agent.user_id,
                        group__is_deleted=False,
                    ),
                    task__status=TaskStatus.ACTIVE,
                    is_completed=False,
                )
                .values_list('task_id', flat=True)
            )
            completed_task_ids = (
                performers
                .by_user(agent.user_id)
                .completed()
                .values_list('task_id', flat=True)
            )
            tasks = (
                Task.objects
                .filter(id__in=task_ids)
                .exclude(id__in=completed_task_ids)
                .order_by('id')
            )
            for task in tasks:
                task_is_blocked = (
                    AIAgentAction.objects
                    .by_agent(agent.id)
                    .by_task(task.id)
                    .type_task()
                    .filter(date_created__gte=task.date_started)
                    .exists()
                )
                if not task_is_blocked:
                    complete_ai_agent_task.delay(
                        task_id=task.id,
                        agent_id=agent.id,
                    )


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

    """ Dispatch the mentions of the active AI agents
        which have no run events of the agent. """

    with periodic_lock('dispatch_ai_agent_new_notifications') as acquired:
        if not acquired:
            return

        notifications = (
            Notification.objects
            .filter(
                type=NotificationType.MENTION,
                user__is_ai=True,
                user__ai_agent__is_active=True,
                user__ai_agent__is_deleted=False,
            )
            .select_related('user__ai_agent')
            .order_by('id')
        )
        for notification in notifications:
            agent_id = notification.user.ai_agent.id
            notification_is_blocked = (
                AIAgentAction.objects
                .by_agent(agent_id)
                .by_notification(notification.id)
                .type_notification()
                .exists()
            )
            if not notification_is_blocked:
                execute_ai_agent_reply.delay(
                    notification_id=notification.id,
                    agent_id=agent_id,
                )
