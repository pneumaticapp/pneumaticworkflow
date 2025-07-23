from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from slack import WebClient
from pneumatic_backend.reports.services.workflows import SendWorkflowsDigest
from pneumatic_backend.reports.services.tasks import SendTasksDigest


UserModel = get_user_model()


@shared_task(ignore_result=True)
def send_digest(user_id=None, force=False, fetch_size=50) -> None:
    sender = SendWorkflowsDigest(
        user_id=user_id,
        force=force,
        fetch_size=fetch_size,
    )
    count_digests_sent = sender.send_digest()
    if (
        not user_id
        and settings.SLACK
        and settings.SLACK_CONFIG['DIGEST_CHANNEL']
    ):
        send_digest_notification.delay(count_digests_sent)


@shared_task(ignore_result=True)
def send_tasks_digest(user_id=None, force=False, fetch_size=50) -> None:
    sender = SendTasksDigest(
        user_id=user_id,
        force=force,
        fetch_size=fetch_size,
    )
    count_digests_sent = sender.send_digest()
    if (
        not user_id
        and settings.SLACK
        and settings.SLACK_CONFIG['DIGEST_CHANNEL']
    ):
        send_tasks_digest_notification.delay(count_digests_sent)


@shared_task
def send_digest_notification(count: int):

    channel = settings.SLACK_CONFIG['DIGEST_CHANNEL']
    token = settings.SLACK_CONFIG['MARVIN_TOKEN']
    text = f'I just sent {count} digests to our users'
    client = WebClient(token=token)
    client.chat_postMessage(
        channel=channel,
        blocks=[
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': text,
                }
            }
        ]
    )


@shared_task
def send_tasks_digest_notification(count: int):

    channel = settings.SLACK_CONFIG['DIGEST_CHANNEL']
    token = settings.SLACK_CONFIG['MARVIN_TOKEN']
    text = f'I just sent {count} "My Tasks" digests to our users'
    client = WebClient(token=token)
    client.chat_postMessage(
        channel=channel,
        blocks=[
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': text,
                }
            }
        ]
    )
