import requests
from django.db.models import ObjectDoesNotExist
from celery.task import Task as CeleryTask
from celery import shared_task
from django.contrib.auth import get_user_model
from pneumatic_backend.webhooks.enums import HookEvent
from pneumatic_backend.webhooks.services import WebhookDeliverer


UserModel = get_user_model()


class WebhookTask(CeleryTask):
    autoretry_for = (
        ConnectionError,
        requests.ConnectionError,
        requests.HTTPError,
        ObjectDoesNotExist
    ),
    retry_backoff = True
    retry_kwargs = {'max_retries': 2}


@shared_task(base=WebhookTask)
def send_workflow_started_webhook(
    user_id: int,
    account_id: int,
    payload: dict,
):
    WebhookDeliverer().send(
        event=HookEvent.WORKFLOW_STARTED,
        user_id=user_id,
        account_id=account_id,
        payload=payload,
    )


@shared_task(base=WebhookTask)
def send_workflow_completed_webhook(
    user_id: int,
    account_id: int,
    payload: dict,
):
    WebhookDeliverer().send(
        event=HookEvent.WORKFLOW_COMPLETED,
        user_id=user_id,
        account_id=account_id,
        payload=payload,
    )


@shared_task(base=WebhookTask)
def send_task_completed_webhook(
    user_id: int,
    account_id: int,
    payload: dict,
):
    WebhookDeliverer().send(
        event=HookEvent.TASK_COMPLETED,
        user_id=user_id,
        account_id=account_id,
        payload=payload,
    )


@shared_task(base=WebhookTask)
def send_task_returned_webhook(
    user_id: int,
    account_id: int,
    payload: dict,
):
    WebhookDeliverer().send(
        event=HookEvent.TASK_RETURNED,
        user_id=user_id,
        account_id=account_id,
        payload=payload,
    )
