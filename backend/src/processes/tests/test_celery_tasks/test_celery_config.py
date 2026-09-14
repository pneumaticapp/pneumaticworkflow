import pytest
import requests
from celery.exceptions import Retry
from django.contrib.auth import get_user_model

from src.celery_app import app
from src.notifications.tasks import (
    NotificationTask,
    send_new_task_notification,
)
from src.processes.tasks.webhooks import (
    WebhookTask,
    send_workflow_started_webhook,
)
from src.webhooks.enums import HookEvent

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_celery_config__testing__always_eager_enabled():

    """ Tests must run tasks in-process, not via the broker. """

    # arrange
    conf = app.conf

    # act
    always_eager = conf.task_always_eager
    eager_propagates = conf.task_eager_propagates

    # assert
    assert always_eager is True
    assert eager_propagates is True


def test_send_workflow_started_webhook__class_autoretry__copied():

    """ Celery 5 keeps autoretry attrs from the Task subclass. """

    # arrange
    task = send_workflow_started_webhook

    # act
    autoretry_for = task.autoretry_for
    retry_backoff = task.retry_backoff
    retry_kwargs = task.retry_kwargs

    # assert
    assert autoretry_for == WebhookTask.autoretry_for
    assert retry_backoff is True
    assert retry_kwargs == {'max_retries': 2}


def test_send_new_task_notification__class_autoretry__copied():

    """ Celery 5 keeps autoretry attrs from the Task subclass. """

    # arrange
    task = send_new_task_notification

    # act
    autoretry_for = task.autoretry_for
    retry_backoff = task.retry_backoff

    # assert
    assert autoretry_for == NotificationTask.autoretry_for
    assert retry_backoff is True


def test_send_workflow_started_webhook__connection_error__retries(
    mocker,
):

    """ Class-attribute autoretry_for still wraps the task body. """

    # arrange
    user_id = 1
    account_id = 1
    payload = {}
    send_mock = mocker.patch(
        'src.processes.tasks.webhooks.WebhookDeliverer.send',
        side_effect=requests.ConnectionError('down'),
    )

    # act
    with pytest.raises(Retry) as ex:
        send_workflow_started_webhook.apply(
            kwargs={
                'user_id': user_id,
                'account_id': account_id,
                'payload': payload,
            },
        )

    # assert
    assert ex.type is Retry
    send_mock.assert_called_once_with(
        event=HookEvent.WORKFLOW_STARTED,
        user_id=user_id,
        account_id=account_id,
        payload=payload,
    )
