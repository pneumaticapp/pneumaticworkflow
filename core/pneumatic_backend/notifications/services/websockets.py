from typing import Dict, Optional
from asyncio import get_event_loop
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from pneumatic_backend.notifications.enums import NotificationMethod
from pneumatic_backend.notifications.services.base import (
    NotificationService,
)
from pneumatic_backend.accounts.enums import UserType
from pneumatic_backend.accounts.models import Notification
from pneumatic_backend.accounts.serializers.notifications import (
    NotificationsSerializer
)
from pneumatic_backend.notifications.consumers import (
    NotificationsConsumer,
    WorkflowEventConsumer,
)

UserModel = get_user_model()


class WebSocketService(NotificationService):

    ALLOWED_METHODS = {
        NotificationMethod.overdue_task,
        NotificationMethod.complete_task,
        NotificationMethod.delay_workflow,
        NotificationMethod.resume_workflow,
        NotificationMethod.due_date_changed,
        NotificationMethod.system,
        NotificationMethod.urgent,
        NotificationMethod.not_urgent,
        NotificationMethod.comment,
        NotificationMethod.mention,
        NotificationMethod.workflow_event,
        NotificationMethod.reaction,
    }

    def _get_serialized_notification(
        self,
        notification: Notification
    ) -> dict:

        # TODO move to higher level for doing this once for all messages

        return NotificationsSerializer(
            instance=notification
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
                    **data
                }
            }
        )

    def _async_send(
        self,
        group_name: str,
        data: Dict[str, str],
    ):

        layer = get_channel_layer()
        loop = get_event_loop()
        loop.create_task(
            layer.group_send(
                group_name,
                {
                    'type': 'notification',
                    'notification': {
                        **data
                    }
                }
            )
        )

    def _send(
        self,
        method_name: NotificationMethod,
        group_name: str,
        data: Dict[str, str],
        sync: bool = False,
    ):
        # TODO Need resolve ws exceptions.
        #  Use "handle_error" method
        self._validate_send(method_name)

        if sync:
            try:
                self._sync_send(group_name=group_name, data=data)
            except RuntimeError:
                self._async_send(group_name=group_name, data=data)
        else:
            self._async_send(group_name=group_name, data=data)

    def _handle_error(self, *args, **kwargs):
        pass

    def send_overdue_task(
        self,
        user_id: int,
        user_type: UserType,
        sync: bool,
        notification: Optional[Notification] = None,
        **kwargs
    ):

        if user_type == UserType.USER:
            self._send(
                method_name=NotificationMethod.overdue_task,
                group_name=f'{NotificationsConsumer.classname}_{user_id}',
                data=self._get_serialized_notification(notification),
                sync=sync
            )

    def send_complete_task(
        self,
        user_id: int,
        sync: bool,
        notification: Optional[Notification] = None,
        **kwargs
    ):
        self._send(
            method_name=NotificationMethod.complete_task,
            group_name=f'{NotificationsConsumer.classname}_{user_id}',
            data=self._get_serialized_notification(notification),
            sync=sync
        )

    def send_resume_workflow(
        self,
        user_id: int,
        sync: bool,
        notification: Optional[Notification] = None,
        **kwargs
    ):

        self._send(
            method_name=NotificationMethod.resume_workflow,
            group_name=f'{NotificationsConsumer.classname}_{user_id}',
            data=self._get_serialized_notification(notification),
            sync=sync
        )

    def send_delay_workflow(
        self,
        user_id: int,
        sync: bool,
        notification: Optional[Notification] = None,
        **kwargs
    ):

        self._send(
            method_name=NotificationMethod.delay_workflow,
            group_name=f'{NotificationsConsumer.classname}_{user_id}',
            data=self._get_serialized_notification(notification),
            sync=sync
        )

    def send_due_date_changed(
        self,
        user_id: int,
        user_type: UserType,
        sync: bool,
        notification: Optional[Notification] = None,
        **kwargs
    ):

        if user_type == UserType.USER:
            self._send(
                method_name=NotificationMethod.due_date_changed,
                group_name=f'{NotificationsConsumer.classname}_{user_id}',
                data=self._get_serialized_notification(notification),
                sync=sync
            )

    def send_system(
        self,
        user_id: int,
        sync: bool,
        notification: Notification,
        **kwargs
    ):
        self._send(
            method_name=NotificationMethod.system,
            group_name=f'{NotificationsConsumer.classname}_{user_id}',
            data=self._get_serialized_notification(notification),
            sync=sync
        )

    def send_urgent(
        self,
        user_id: int,
        sync: bool,
        notification: Notification,
        **kwargs
    ):
        self._send(
            method_name=NotificationMethod.urgent,
            group_name=f'{NotificationsConsumer.classname}_{user_id}',
            data=self._get_serialized_notification(notification),
            sync=sync
        )

    def send_not_urgent(
        self,
        user_id: int,
        sync: bool,
        notification: Notification,
        **kwargs
    ):
        self._send(
            method_name=NotificationMethod.not_urgent,
            group_name=f'{NotificationsConsumer.classname}_{user_id}',
            data=self._get_serialized_notification(notification),
            sync=sync
        )

    def send_mention(
        self,
        user_id: int,
        sync: bool,
        notification: Notification,
        **kwargs
    ):
        self._send(
            method_name=NotificationMethod.mention,
            group_name=f'{NotificationsConsumer.classname}_{user_id}',
            data=self._get_serialized_notification(notification),
            sync=sync
        )

    def send_comment(
        self,
        user_id: int,
        sync: bool,
        notification: Notification,
        **kwargs
    ):
        self._send(
            method_name=NotificationMethod.comment,
            group_name=f'{NotificationsConsumer.classname}_{user_id}',
            data=self._get_serialized_notification(notification),
            sync=sync
        )

    def send_workflow_event(
        self,
        user_id: int,
        data: dict,
        sync: bool,
    ):
        self._send(
            method_name=NotificationMethod.workflow_event,
            group_name=f'{WorkflowEventConsumer.classname}_{user_id}',
            data=data,
            sync=sync
        )

    def send_reaction(
        self,
        user_id: int,
        sync: bool,
        notification: Notification,
        **kwargs
    ):
        self._send(
            method_name=NotificationMethod.reaction,
            group_name=f'{NotificationsConsumer.classname}_{user_id}',
            data=self._get_serialized_notification(notification),
            sync=sync
        )
