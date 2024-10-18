import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_account,
)
from pneumatic_backend.notifications.tasks import (
    _send_reaction_notification
)
from pneumatic_backend.accounts.enums import (
    NotificationType,
)
from pneumatic_backend.accounts.models import Notification
from pneumatic_backend.notifications.messages import MSG_NF_0001
from pneumatic_backend.notifications.services.push import (
    PushNotificationService
)


pytestmark = pytest.mark.django_db


def test_send_reaction_notification__call_services__ok(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    reacted_user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False,
        first_name='Messaged',
        last_name='User'
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(reacted_user)
    push_notification_service_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None
    )
    push_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.push.'
        'PushNotificationService.send_reaction'
    )
    websocket_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_reaction'
    )
    reaction = ':dumb face:'

    # act
    _send_reaction_notification(
        logging=account.log_api_requests,
        author_id=reacted_user.id,
        author_name=reacted_user.name,
        task_id=task.id,
        user_id=account_owner.id,
        account_id=account.id,
        reaction=reaction,
        workflow_name=workflow.name,
    )

    # assert
    text = MSG_NF_0001(reaction)
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=account_owner.id,
        author_id=reacted_user.id,
        account_id=account.id,
        type=NotificationType.REACTION,
        text=text
    )
    push_notification_service_mock.assert_called_once_with(
        logging=account.log_api_requests
    )
    push_kwargs = {
        'sync': True,
        'notification': notification,
    }
    push_notification_mock.assert_called_once_with(
        task_id=task.id,
        user_id=account_owner.id,
        author_name='Messaged User',
        workflow_name=workflow.name,
        text=text,
        **push_kwargs
    )
    websocket_kwargs = {
        'task_id': task.id,
        'text': text,
        'author_name': 'Messaged User',
        'workflow_name': workflow.name,
    }
    websocket_notification_mock.assert_called_once_with(
        user_id=account_owner.id,
        sync=True,
        notification=notification,
        **websocket_kwargs,
    )
