import pytest
from src.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_account,
)
from src.notifications.tasks import (
    _send_delayed_workflow_notification
)
from src.accounts.enums import (
    NotificationType,
)
from src.accounts.models import Notification
from src.notifications.services.push import (
    PushNotificationService
)


pytestmark = pytest.mark.django_db


def test_send_delayed_workflow_notification__call_services__ok(mocker):

    # arrange
    account = create_test_account(
        log_api_requests=True,
        logo_lg='https://logo.jpg'
    )
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    push_notification_service_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None
    )
    push_notification_mock = mocker.patch(
        'src.notifications.services.push.'
        'PushNotificationService.send_delay_workflow'
    )
    websocket_notification_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_delay_workflow'
    )

    # act
    _send_delayed_workflow_notification(
        logging=account.log_api_requests,
        author_id=account_owner.id,
        user_id=user.id,
        user_email=user.email,
        account_id=account.id,
        task_id=task.id,
        logo_lg=account.logo_lg,
    )

    # assert
    notification = Notification.objects.get(
        task_id=task.id,
        author_id=account_owner.id,
        user_id=user.id,
        account_id=account.id,
        type=NotificationType.DELAY_WORKFLOW,
    )
    push_notification_service_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    push_notification_mock.assert_called_once_with(
        notification=notification,
        user_id=user.id,
        user_email=user.email,
        task_id=task.id,
        workflow_name=workflow.name,
        author_id=account_owner.id,
        sync=True,
    )
    websocket_notification_mock.assert_called_once_with(
        notification=notification,
        user_id=user.id,
        user_email=user.email,
        task_id=task.id,
        workflow_name=workflow.name,
        author_id=account_owner.id,
        sync=True
    )
