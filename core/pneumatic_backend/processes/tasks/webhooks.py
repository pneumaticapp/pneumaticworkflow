from celery import shared_task
from django.contrib.auth import get_user_model
from rest_hooks.signals import raw_hook_event

from pneumatic_backend.processes.models import Workflow, Task

UserModel = get_user_model()


def _send_webhook(event_name: str, user_id: int, instance):

    raw_hook_event.send(
        sender=instance.__class__,
        event_name=event_name,
        payload=None,
        user=UserModel.include_inactive.by_id(user_id).first(),
        instance=instance
    )


@shared_task
def send_workflow_started_webhook(user_id: int, instance_id: int):
    _send_webhook(
        event_name='workflow_started',
        user_id=user_id,
        instance=Workflow.objects.get(id=instance_id)
    )


@shared_task
def send_workflow_completed_webhook(user_id: int, instance_id: int):
    _send_webhook(
        event_name='workflow_completed',
        user_id=user_id,
        instance=Workflow.objects.get(id=instance_id)
    )


# TODO Deprecated, use specific tasks instead of common
@shared_task
def send_workflow_webhook(event_name: str, user_id: int, instance_id: int):
    _send_webhook(event_name, user_id, Workflow.objects.get(id=instance_id))


@shared_task
def send_task_webhook(event_name: str, user_id: int, instance_id: int):
    _send_webhook(event_name, user_id, Task.objects.get(id=instance_id))
