import pytest

from pneumatic_backend.notifications.services.push import \
    PushNotificationService
from pneumatic_backend.notifications.tasks import (
    _send_complete_task_notification
)
from pneumatic_backend.notifications.enums import NotificationMethod
from pneumatic_backend.accounts.enums import NotificationType
from pneumatic_backend.accounts.models import Notification
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_account,
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
        account=account
    )
    user = create_test_user(
        email=user_email,
        account=account,
        is_account_owner=False
    )
    workflow = create_test_workflow(user, name=workflow_name, tasks_count=1)
    task = workflow.current_task_instance

    push_notification_service_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None
    )
    push_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.push.'
        'PushNotificationService.send_complete_task'
    )
    ws_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_complete_task'
    )

    # act
    _send_complete_task_notification(
        logging=account.log_api_requests,
        author_id=account_owner.id,
        account_id=account.id,
        recipients=[(user.id, user_email)],
        task_id=task.id,
        task_name=task.name,
        workflow_name=workflow_name,
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
    )
    push_kwargs = {
        'sync': True,
        'user_email': user_email,
        'logo_lg': logo_lg,
        'notification': notification
    }
    push_notification_mock.assert_called_once_with(
        task_id=task.id,
        task_name=task.name,
        workflow_name=workflow_name,
        user_id=user.id,
        **push_kwargs
    )
    ws_kwargs = {
        'user_email': user_email,
        'logo_lg': logo_lg,
        'workflow_name': workflow_name,
        'task_id': task.id,
        'task_name': task.name,
    }
    ws_notification_mock.assert_called_once_with(
        user_id=user.id,
        sync=True,
        notification=notification,
        **ws_kwargs
    )


def test_send_complete_task_notification__ok(api_client, mocker):

    # arrange
    logo_lg = 'https://photo.com/logo.jpg'
    user_email = 'test@test.test'
    workflow_name = 'Workflow name'

    account = create_test_account(logo_lg=logo_lg, log_api_requests=True)
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    user = create_test_user(
        email=user_email,
        account=account,
        is_account_owner=False
    )
    workflow = create_test_workflow(user, name=workflow_name, tasks_count=1)
    task = workflow.current_task_instance

    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )

    # act
    _send_complete_task_notification(
        logging=account.log_api_requests,
        author_id=account_owner.id,
        account_id=account.id,
        recipients=[(user.id, user_email)],
        task_id=task.id,
        task_name=task.name,
        workflow_name=workflow_name,
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
    send_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        notification=notification,
        method_name=NotificationMethod.complete_task,
        user_id=user.id,
        user_email=user_email,
        logo_lg=logo_lg,
        workflow_name=workflow_name,
        task_id=task.id,
        task_name=task.name,
        sync=True
    )
