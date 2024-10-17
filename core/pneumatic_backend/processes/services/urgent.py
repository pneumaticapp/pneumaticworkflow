from typing import Optional
from django.utils import timezone as tz
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.models import WorkflowEvent
from pneumatic_backend.notifications.tasks import (
    send_urgent_notification,
    send_not_urgent_notification,
)
from pneumatic_backend.processes.enums import WorkflowEventType
from pneumatic_backend.accounts.enums import NotificationType
from pneumatic_backend.accounts.models import Notification
from pneumatic_backend.processes.models import (
    Workflow,
)
from pneumatic_backend.processes.api_v2.services import (
    WorkflowEventService
)


UserModel = get_user_model()


class UrgentService:

    @classmethod
    def _get_event_type(cls, workflow: Workflow) -> WorkflowEventType:
        return (
            WorkflowEventType.URGENT if workflow.is_urgent
            else WorkflowEventType.NOT_URGENT
        )

    @classmethod
    def _get_notification_type(
        cls,
        workflow: Workflow,
        reverse: bool = False
    ) -> NotificationType:
        if reverse:
            return (
                NotificationType.NOT_URGENT if workflow.is_urgent
                else NotificationType.URGENT
            )
        else:
            return (
                NotificationType.URGENT if workflow.is_urgent
                else NotificationType.NOT_URGENT
            )

    @classmethod
    def _get_prev_urgent_event(
        cls,
        workflow: Workflow
    ) -> Optional[WorkflowEvent]:

        return WorkflowEvent.objects.on_workflow(
            workflow.id
        ).filter(
            type__in=WorkflowEventType.URGENT_TYPES
        ).last_created()

    @classmethod
    def _delete_urgent_notification(
        cls,
        workflow: Workflow,
        user: UserModel
    ):

        notification = Notification.objects.filter(
            user=user,
            type=cls._get_notification_type(workflow, reverse=True),
            task__workflow=workflow
        ).last_created()
        if notification:
            notification.delete()

    @classmethod
    def _create_urgent_actions(
        cls,
        workflow: Workflow,
        user: UserModel
    ):
        event_type = cls._get_event_type(workflow)
        notification_type = cls._get_notification_type(workflow)
        if notification_type == NotificationType.URGENT:
            send_urgent_notification.delay(
                author_id=user.id,
                task_id=workflow.current_task_instance.id,
                account_id=user.account_id
            )
        else:
            send_not_urgent_notification.delay(
                author_id=user.id,
                task_id=workflow.current_task_instance.id,
                account_id=user.account_id
            )
        WorkflowEventService.workflow_urgent_event(
            event_type=event_type,
            workflow=workflow,
            user=user,
        )

    @classmethod
    def resolve(
        cls,
        workflow: Workflow,
        user: UserModel
    ):

        """ Urgent management logic:
        1. If previous urgent event not exists - create new event
        2. If previous urgent event exists:
            2.1 The previous event is of the same type - not create new
            2.2 The previous event has different type
                and creation time less then 1 min - not create new event
                and delete previous event
            2.3 The previous event has different type
                and creation time more then 1 min - create new event """

        prev_urgent_event = cls._get_prev_urgent_event(workflow)
        if not prev_urgent_event:
            cls._create_urgent_actions(workflow, user)
        else:
            if prev_urgent_event.type != cls._get_event_type(workflow):
                delete_period = tz.now() - tz.timedelta(minutes=1)
                if prev_urgent_event.created >= delete_period:
                    prev_urgent_event.delete()
                    cls._delete_urgent_notification(workflow, user)
                else:
                    cls._create_urgent_actions(workflow, user)
