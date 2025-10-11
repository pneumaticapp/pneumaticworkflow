import pytest
from src.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_account,
)
from src.processes.models import WorkflowEvent
from src.processes.enums import WorkflowEventType
from src.processes.serializers.workflows.events import (
    TaskEventJsonSerializer,
)
from src.notifications.tasks import (
    _send_comment_notification,
)
from src.accounts.enums import (
    NotificationType,
)
from src.accounts.models import Notification
from src.notifications.services.push import (
    PushNotificationService,
)


pytestmark = pytest.mark.django_db


def test_send_comment_notification__call_services__ok(mocker):

    # arrange
    account = create_test_account(
        log_api_requests=True,
        logo_lg='https://logo.jpg',
    )
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False,
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.performers.add(account_owner)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=task,
        task_json=TaskEventJsonSerializer(
            instance=task,
            context={'event_type': WorkflowEventType.COMMENT},
        ).data,
        user=account_owner,
    )
    push_notification_service_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None,
    )
    push_notification_mock = mocker.patch(
        'src.notifications.services.push.'
        'PushNotificationService.send_comment',
    )
    websocket_notification_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_comment',
    )
    text = 'Some comment'

    # act
    _send_comment_notification(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
        author_id=user.id,
        event_id=event.id,
        users_ids=(account_owner.id,),
        text=text,
    )

    # assert
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=account_owner.id,
        author_id=user.id,
        account_id=account.id,
        type=NotificationType.COMMENT,
        text=text,
    )
    push_notification_service_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    push_notification_mock.assert_called_once_with(
        task_id=task.id,
        user_id=account_owner.id,
        user_email=account_owner.email,
        sync=True,
        notification=notification,
    )
    websocket_notification_mock.assert_called_once_with(
        task_id=task.id,
        user_id=account_owner.id,
        user_email=account_owner.email,
        sync=True,
        notification=notification,
    )
