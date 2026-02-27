import pytest
from django.conf import settings

from src.accounts.enums import NotificationType
from src.accounts.models import Notification
from src.notifications.enums import NotificationMethod
from src.notifications.services.push import PushNotificationService
from src.notifications.tasks import (
    _send_complete_task_notification,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_user,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_send_complete_task_notification__call_services(mocker):

    # arrange
    logo_lg = 'https://photo.com/logo.jpg'
    user_email = 'test@test.test'
    workflow_name = 'Workflow name'

    account = create_test_account(logo_lg=logo_lg, log_api_requests=True)
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    user = create_test_user(
        email=user_email,
        account=account,
        is_account_owner=False,
    )
    workflow = create_test_workflow(user, name=workflow_name, tasks_count=1)
    task = workflow.tasks.get(number=1)

    push_notification_service_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None,
    )
    push_notification_mock = mocker.patch(
        'src.notifications.services.push.'
        'PushNotificationService.send_complete_task',
    )
    ws_notification_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_complete_task',
    )

    # act
    _send_complete_task_notification(
        logging=account.log_api_requests,
        author_id=account_owner.id,
        account_id=account.id,
        recipients=[(user.id, user_email)],
        task_id=task.id,
        logo_lg=logo_lg,
    )

    # assert
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=user.id,
        author_id=account_owner.id,
        account_id=account.id,
        type=NotificationType.COMPLETE_TASK,
    )
    push_notification_service_mock.assert_called_once_with(
        logging=account.log_api_requests,
        logo_lg=logo_lg,
        account_id=account.id,
    )
    link = f'{settings.FRONTEND_URL}/tasks/{task.id}'
    push_notification_mock.assert_called_once_with(
        task_id=task.id,
        task_name=task.name,
        workflow_name=workflow_name,
        user_id=user.id,
        sync=True,
        user_email=user_email,
        notification=notification,
        link=link,
    )
    ws_notification_mock.assert_called_once_with(
        task_id=task.id,
        task_name=task.name,
        workflow_name=workflow_name,
        user_id=user.id,
        sync=True,
        user_email=user_email,
        notification=notification,
        link=link,
    )


def test_send_complete_task_notification__ok(api_client, mocker):

    # arrange
    logo_lg = 'https://photo.com/logo.jpg'
    user_email = 'test@test.test'
    workflow_name = 'Workflow name'

    account = create_test_account(logo_lg=logo_lg, log_api_requests=True)
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    user = create_test_user(
        email=user_email,
        account=account,
        is_account_owner=False,
    )
    workflow = create_test_workflow(user, name=workflow_name, tasks_count=1)
    task = workflow.tasks.get(number=1)

    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_complete_task_notification(
        logging=account.log_api_requests,
        author_id=account_owner.id,
        account_id=account.id,
        recipients=[(user.id, user_email)],
        task_id=task.id,
        logo_lg=logo_lg,
    )

    # assert
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=user.id,
        author_id=account_owner.id,
        account_id=account.id,
        type=NotificationType.COMPLETE_TASK,
    )
    link = f'{settings.FRONTEND_URL}/tasks/{task.id}'
    send_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        logo_lg=logo_lg,
        user_id=user.id,
        user_email=user_email,
        account_id=account.id,
        notification=notification,
        method_name=NotificationMethod.complete_task,
        workflow_name=workflow_name,
        task_id=task.id,
        task_name=task.name,
        link=link,
        sync=True,
    )
