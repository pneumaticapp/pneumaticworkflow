import uuid
from asyncio import get_event_loop
from typing import Dict, Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.utils import timezone

from src.accounts.enums import UserType
from src.accounts.models import Notification
from src.accounts.serializers.notifications import (
    NotificationsSerializer,
)
from src.notifications.consumers import (
    EventsConsumer,
)
from src.notifications.enums import NotificationMethod
from src.notifications.services.base import (
    NotificationService,
)

UserModel = get_user_model()


class WebSocketService(NotificationService):

    ALLOWED_METHODS = {
        NotificationMethod.overdue_task,
        NotificationMethod.task_completed,
        NotificationMethod.delay_workflow,
        NotificationMethod.resume_workflow,
        NotificationMethod.due_date_changed,
        NotificationMethod.system,
        NotificationMethod.urgent,
        NotificationMethod.not_urgent,
        NotificationMethod.comment,
        NotificationMethod.mention,
        NotificationMethod.workflow_event,
        NotificationMethod.event_created,
        NotificationMethod.event_updated,
        NotificationMethod.reaction,
        NotificationMethod.new_task_websocket,
        NotificationMethod.task_deleted,
        NotificationMethod.group_created,
        NotificationMethod.group_updated,
        NotificationMethod.group_deleted,
        NotificationMethod.user_created,
        NotificationMethod.user_updated,
        NotificationMethod.user_deleted,
        NotificationMethod.task_created,
        NotificationMethod.notification_created,
    }

    def _get_serialized_notification(
        self,
        notification: Notification,
    ) -> dict:

        # TODO move to higher level for doing this once for all messages

        return NotificationsSerializer(
            instance=notification,
        ).data

    def _sync_send(
        self,
        group_name: str,
        data: Dict[str, str],
    ):
        layer = get_channel_layer()
        async_to_sync(layer.group_send)(
            group_name,
            {
                'type': 'notification',
                'notification': {
                    **data,
                },
            },
        )

    def _async_send(
        self,
        group_name: str,
        data: Dict[str, str],
    ):
        background_tasks = set()
        layer = get_channel_layer()
        loop = get_event_loop()
        task = loop.create_task(
            layer.group_send(
                group_name,
                {
                    'type': 'notification',
                    'notification': {
                        **data,
                    },
                },
            ),
        )
        task.add_done_callback(background_tasks.discard)

    def _send(
        self,
        method_name: NotificationMethod,
        group_name: str,
        message_type: str,
        data: Dict[str, str],
        sync: bool = False,
    ):
        # TODO Need resolve ws exceptions.
        #  Use "handle_error" method
        self._validate_send(method_name)

        message = {
            'id': str(uuid.uuid4()),
            'date_created_tsp': timezone.now().timestamp(),
            'type': message_type,
            'data': data,
        }

        if sync:
            try:
                self._sync_send(group_name=group_name, data=message)
            except RuntimeError:
                self._async_send(group_name=group_name, data=message)
        else:
            self._async_send(group_name=group_name, data=message)

    def _handle_error(self, *args, **kwargs):
        pass

    def send_overdue_task(
        self,
        user_id: int,
        user_type: UserType,
        sync: bool,
        notification: Optional[Notification] = None,
        **kwargs,
    ):

        if user_type == UserType.USER:
            self._send(
                method_name=NotificationMethod.overdue_task,
                group_name=f'{EventsConsumer.classname}_{user_id}',
                message_type=NotificationMethod.notification_created,
                data=self._get_serialized_notification(notification),
                sync=sync,
            )

    def send_task_completed(
        self,
        user_id: int,
        sync: bool,
        notification: Optional[Notification] = None,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.task_completed,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.task_completed,
            data=self._get_serialized_notification(notification),
            sync=sync,
        )

    def send_resume_workflow(
        self,
        user_id: int,
        sync: bool,
        notification: Optional[Notification] = None,
        **kwargs,
    ):

        self._send(
            method_name=NotificationMethod.resume_workflow,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.notification_created,
            data=self._get_serialized_notification(notification),
            sync=sync,
        )

    def send_delay_workflow(
        self,
        user_id: int,
        sync: bool,
        notification: Optional[Notification] = None,
        **kwargs,
    ):

        self._send(
            method_name=NotificationMethod.delay_workflow,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.notification_created,
            data=self._get_serialized_notification(notification),
            sync=sync,
        )

    def send_due_date_changed(
        self,
        user_id: int,
        user_type: UserType,
        sync: bool,
        notification: Optional[Notification] = None,
        **kwargs,
    ):

        if user_type == UserType.USER:
            self._send(
                method_name=NotificationMethod.due_date_changed,
                group_name=f'{EventsConsumer.classname}_{user_id}',
                message_type=NotificationMethod.notification_created,
                data=self._get_serialized_notification(notification),
                sync=sync,
            )

    def send_system(
        self,
        user_id: int,
        sync: bool,
        notification: Notification,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.system,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.notification_created,
            data=self._get_serialized_notification(notification),
            sync=sync,
        )

    def send_urgent(
        self,
        user_id: int,
        sync: bool,
        notification: Notification,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.urgent,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.notification_created,
            data=self._get_serialized_notification(notification),
            sync=sync,
        )

    def send_not_urgent(
        self,
        user_id: int,
        sync: bool,
        notification: Notification,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.not_urgent,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.notification_created,
            data=self._get_serialized_notification(notification),
            sync=sync,
        )

    def send_mention(
        self,
        user_id: int,
        sync: bool,
        notification: Notification,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.mention,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.notification_created,
            data=self._get_serialized_notification(notification),
            sync=sync,
        )

    def send_comment(
        self,
        user_id: int,
        sync: bool,
        notification: Notification,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.comment,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.notification_created,
            data=self._get_serialized_notification(notification),
            sync=sync,
        )

    def send_event_created(
        self,
        user_id: int,
        data: dict,
        sync: bool,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.event_created,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.event_created,
            data=data,
            sync=sync,
        )

    def send_event_updated(
        self,
        user_id: int,
        data: dict,
        sync: bool,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.event_updated,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.event_updated,
            data=data,
            sync=sync,
        )

    def send_reaction(
        self,
        user_id: int,
        sync: bool,
        notification: Notification,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.reaction,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.notification_created,
            data=self._get_serialized_notification(notification),
            sync=sync,
        )

    def send_new_task_websocket(
        self,
        user_id: int,
        task_data: dict,
        sync: bool,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.task_created,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.task_created,
            data=task_data,
            sync=sync,
        )

    def send_task_deleted(
        self,
        user_id: int,
        task_data: dict,
        sync: bool,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.task_deleted,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.task_deleted,
            data=task_data,
            sync=sync,
        )

    def send_group_created(
        self,
        user_id: int,
        group_data: dict,
        sync: bool,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.group_created,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.group_created,
            data=group_data,
            sync=sync,
        )

    def send_group_updated(
        self,
        user_id: int,
        group_data: dict,
        sync: bool,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.group_updated,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.group_updated,
            data=group_data,
            sync=sync,
        )

    def send_group_deleted(
        self,
        user_id: int,
        group_data: dict,
        sync: bool,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.group_deleted,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.group_deleted,
            data=group_data,
            sync=sync,
        )

    def send_user_created(
        self,
        user_id: int,
        user_data: dict,
        sync: bool,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.user_created,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.user_created,
            data=user_data,
            sync=sync,
        )

    def send_user_updated(
        self,
        user_id: int,
        user_data: dict,
        sync: bool,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.user_updated,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.user_updated,
            data=user_data,
            sync=sync,
        )

    def send_user_deleted(
        self,
        user_id: int,
        user_data: dict,
        sync: bool,
        **kwargs,
    ):
        self._send(
            method_name=NotificationMethod.user_deleted,
            group_name=f'{EventsConsumer.classname}_{user_id}',
            message_type=NotificationMethod.user_deleted,
            data=user_data,
            sync=sync,
        )
