import pytest

from src.accounts.enums import (
    NotificationType,
)
from src.accounts.models import Notification
from src.accounts.serializers.notifications import (
    NotificationTaskSerializer,
    NotificationWorkflowSerializer,
)
from src.notifications.messages import MSG_NF_0001
from src.notifications.services.push import (
    PushNotificationService,
)
from src.notifications.tasks import (
    _send_reaction_notification,
)
from src.processes.enums import WorkflowEventType
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.serializers.workflows.events import (
    TaskEventJsonSerializer,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_user,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_send_reaction_notification__call_services__ok(mocker):

    # arrange
    account = create_test_account(logo_lg='https://logo.jpg')
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    reacted_user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False,
        first_name='Messaged',
        last_name='User',
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.performers.add(reacted_user)
    event = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        task=task,
        task_json=TaskEventJsonSerializer(
            instance=task,
            context={'event_type': WorkflowEventType.COMMENT},
        ).data,
        workflow=workflow,
        user=reacted_user,
        text='Test comment',
    )
    push_notification_service_init_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None,
    )
    push_notification_mock = mocker.patch(
        'src.notifications.services.push.'
        'PushNotificationService.send_reaction',
    )
    websocket_notification_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_reaction',
    )
    reaction = ':dumb face:'

    # act
    _send_reaction_notification(
        logging=account.log_api_requests,
        author_id=reacted_user.id,
        author_name=reacted_user.name,
        user_id=account_owner.id,
        user_email=account_owner.email,
        logo_lg=account.logo_lg,
        account_id=account.id,
        reaction=reaction,
        event_id=event.id,
    )

    # assert
    text = MSG_NF_0001(reaction)
    notification = Notification.objects.get(
        task_id=task.id,
        task_json=NotificationTaskSerializer(
            instance=event.task,
            notification_type=NotificationType.REACTION,
        ).data,
        workflow_json=NotificationWorkflowSerializer(
            instance=event.workflow,
        ).data,
        user_id=account_owner.id,
        author_id=reacted_user.id,
        account_id=account.id,
        type=NotificationType.REACTION,
        text=text,
    )
    push_notification_service_init_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    link = f'http://localhost/tasks/{task.id}'
    push_notification_mock.assert_called_once_with(
        task_id=task.id,
        user_id=account_owner.id,
        user_email=account_owner.email,
        author_name='Messaged User',
        workflow_name=workflow.name,
        text=text,
        sync=True,
        notification=notification,
        link=link,
    )
    websocket_notification_mock.assert_called_once_with(
        task_id=task.id,
        user_id=account_owner.id,
        user_email=account_owner.email,
        author_name='Messaged User',
        workflow_name=workflow.name,
        text=text,
        sync=True,
        notification=notification,
        link=link,
    )


def test_send_reaction_notification__delete_task__ok(mocker):

    # arrange
    account = create_test_account(logo_lg='https://logo.jpg')
    account_owner = create_test_user(
        is_account_owner=True,
        account=account,
    )
    reacted_user = create_test_user(
        email='t@t.t',
        account=account,
        is_account_owner=False,
        first_name='Messaged',
        last_name='User',
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.performers.add(reacted_user)
    event = WorkflowEvent.objects.create(
        type=WorkflowEventType.COMMENT,
        account=account,
        task=task,
        task_json=TaskEventJsonSerializer(
            instance=task,
            context={'event_type': WorkflowEventType.COMMENT},
        ).data,
        workflow=workflow,
        user=reacted_user,
        text='Test comment',
    )
    task.delete()
    push_notification_service_init_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None,
    )
    push_notification_mock = mocker.patch(
        'src.notifications.services.push.'
        'PushNotificationService.send_reaction',
    )
    websocket_notification_mock = mocker.patch(
        'src.notifications.services.websockets.'
        'WebSocketService.send_reaction',
    )
    reaction = ':dumb face:'

    # act
    _send_reaction_notification(
        logging=account.log_api_requests,
        author_id=reacted_user.id,
        author_name=reacted_user.name,
        user_id=account_owner.id,
        user_email=account_owner.email,
        logo_lg=account.logo_lg,
        account_id=account.id,
        reaction=reaction,
        event_id=event.id,
    )

    # assert
    text = MSG_NF_0001(reaction)
    notification = Notification.objects.get(
        task_id=task.id,
        task_json={
            'id': event.task_json['id'],
            'name': event.task_json['name'],
        },
        workflow_json=NotificationWorkflowSerializer(
            instance=event.workflow,
        ).data,
        user_id=account_owner.id,
        author_id=reacted_user.id,
        account_id=account.id,
        type=NotificationType.REACTION,
        text=text,
    )
    push_notification_service_init_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    link = f'http://localhost/tasks/{task.id}'
    push_notification_mock.assert_called_once_with(
        task_id=task.id,
        user_id=account_owner.id,
        user_email=account_owner.email,
        author_name='Messaged User',
        workflow_name=workflow.name,
        text=text,
        sync=True,
        notification=notification,
        link=link,
    )
    websocket_notification_mock.assert_called_once_with(
        task_id=task.id,
        user_id=account_owner.id,
        user_email=account_owner.email,
        author_name='Messaged User',
        workflow_name=workflow.name,
        text=text,
        sync=True,
        notification=notification,
        link=link,
    )
