import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_account,
)
from pneumatic_backend.processes.models import WorkflowEvent
from pneumatic_backend.processes.enums import WorkflowEventType
from pneumatic_backend.processes.api_v2.serializers.workflow.events import (
    TaskEventJsonSerializer
)
from pneumatic_backend.notifications.tasks import (
    _send_mention_notification
)
from pneumatic_backend.accounts.enums import (
    NotificationType,
)
from pneumatic_backend.accounts.models import Notification
from pneumatic_backend.notifications.services.push import (
    PushNotificationService
)
from pneumatic_backend.notifications.services.email import EmailService
from pneumatic_backend.notifications.services.websockets import (
    WebSocketService
)


pytestmark = pytest.mark.django_db


def test_send_mention_notification__call_services__ok(mocker):

    # arrange
    account = create_test_account(
        log_api_requests=True,
        logo_lg='https://logo.jpg',
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
    task = workflow.current_task_instance
    task.performers.add(account_owner)
    event = WorkflowEvent.objects.create(
        account=account,
        type=WorkflowEventType.COMMENT,
        text='Old text',
        with_attachments=False,
        workflow=workflow,
        task=workflow.current_task_instance,
        task_json=TaskEventJsonSerializer(
            instance=task,
            context={'event_type': WorkflowEventType.COMMENT}
        ).data,
        user=account_owner,
    )
    push_notification_service_init_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None
    )
    push_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.push.'
        'PushNotificationService.send_mention'
    )
    websocket_service_init_mock = mocker.patch.object(
        WebSocketService,
        attribute='__init__',
        return_value=None
    )
    websocket_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_mention'
    )
    email_service_init_mock = mocker.patch.object(
        EmailService,
        attribute='__init__',
        return_value=None
    )
    email_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.'
        'EmailService.send_mention'
    )
    text = 'Some mention'

    # act
    _send_mention_notification(
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
        type=NotificationType.MENTION,
        text=text
    )
    push_notification_service_init_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    push_notification_mock.assert_called_once_with(
        task_id=task.id,
        user_id=account_owner.id,
        user_email=account_owner.email,
        user_first_name=account_owner.first_name,
        notification=notification,
        sync=True,
    )
    websocket_service_init_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    websocket_notification_mock.assert_called_once_with(
        task_id=task.id,
        user_id=account_owner.id,
        user_email=account_owner.email,
        user_first_name=account_owner.first_name,
        notification=notification,
        sync=True,
    )
    email_service_init_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    email_notification_mock.assert_called_once_with(
        task_id=task.id,
        user_id=account_owner.id,
        user_email=account_owner.email,
        user_first_name=account_owner.first_name,
        notification=notification,
        sync=True,
    )
