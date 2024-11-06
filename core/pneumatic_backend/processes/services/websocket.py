from asyncio import get_event_loop
from typing import Type, Iterable, Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from pneumatic_backend.consumers import PneumaticBaseConsumer
from pneumatic_backend.notifications.consumers import (
    NewTaskConsumer,
    RemovedTaskConsumer,
)
from pneumatic_backend.processes.models import Task, TaskForList
from pneumatic_backend.processes.api_v2.serializers.workflow.task import (
    TaskListSerializer
)
from django.contrib.auth import get_user_model


UserModel = get_user_model()


class WSSender:

    # TODO: move to notifications app https://my.pneumatic.app/workflows/15592

    @classmethod
    def send(cls, group_name, data):
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

    @classmethod
    def sync_send(cls, group_name, data):
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

    @classmethod
    def _send_task_notification(
        cls,
        task: Task,
        consumer_cls: Type[PneumaticBaseConsumer],
        sync: bool = False,
        user_ids: Optional[Iterable[int]] = None
    ):

        """ user_ids - specify the list of notification receivers,
            default all task performers """

        send = cls.sync_send if sync else cls.send
        task_for_list = TaskForList(
            id=task.id,
            name=task.name,
            date_started=task.date_started,
            date_started_tsp=(
                task.date_started.timestamp()
                if task.date_started else None
            ),
            date_completed=task.date_completed,
            date_completed_tsp=(
                task.date_completed.timestamp()
                if task.date_completed else None
            ),
            due_date=task.due_date,
            due_date_tsp=(
                task.due_date.timestamp()
                if task.due_date else None
            ),
            workflow_name=task.workflow.name,
            template_task_id=task.template_id,
            template_id=task.workflow.template_id,
            is_urgent=task.is_urgent
        )
        task_data = TaskListSerializer(instance=task_for_list).data

        if user_ids is None:
            user_ids = task.performers.exclude_directly_deleted(
            ).active().only_ids()
        for user_id in user_ids:
            send(
                group_name=f'{consumer_cls.classname}_{user_id}',
                data=task_data,
            )

    @classmethod
    def send_new_task_notification(
        cls,
        task: Task,
        sync: bool = False,
        user_ids: Optional[Iterable[int]] = None
    ):

        """ The notification about the need to add
            the task to the list """

        cls._send_task_notification(
            task=task,
            consumer_cls=NewTaskConsumer,
            sync=sync,
            user_ids=user_ids
        )

    @classmethod
    def send_removed_task_notification(
        cls,
        task: Task,
        sync: bool = False,
        user_ids: Optional[Iterable[int]] = None
    ):

        """ The notification about the need to remove
            the task from the list """

        cls._send_task_notification(
            task=task,
            consumer_cls=RemovedTaskConsumer,
            sync=sync,
            user_ids=user_ids
        )
