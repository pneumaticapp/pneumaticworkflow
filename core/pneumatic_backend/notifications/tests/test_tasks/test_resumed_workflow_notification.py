import pytest
from django.utils import timezone
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_account,
    create_test_guest,
)
from pneumatic_backend.notifications.tasks import (
    _send_resumed_workflow_notification
)
from pneumatic_backend.accounts.enums import (
    NotificationType,
)
from pneumatic_backend.accounts.models import Notification
from pneumatic_backend.processes.models import TaskPerformer
from pneumatic_backend.processes.enums import DirectlyStatus
from pneumatic_backend.notifications.enums import (
    NotificationMethod,
)
from pneumatic_backend.notifications.services.push import (
    PushNotificationService
)


pytestmark = pytest.mark.django_db


def test_send_resumed_workflow_notification__call_services__ok(mocker):

    # arrange
    account = create_test_account(log_api_requests=True)
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
    push_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.push.'
        'PushNotificationService.send_resume_workflow'
    )
    websocket_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_resume_workflow'
    )
    push_notification_service_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None
    )

    # act
    _send_resumed_workflow_notification(
        logging=account.log_api_requests,
        task_id=task.id,
        author_id=account_owner.id,
        account_id=account.id,
        workflow_name=workflow.name
    )

    # assert
    notification = Notification.objects.get(
        task_id=task.id,
        author_id=account_owner.id,
        user_id=user.id,
        account_id=account.id,
        type=NotificationType.RESUME_WORKFLOW,
    )
    push_notification_service_mock.assert_called_once_with(
        logging=account.log_api_requests
    )
    push_notification_mock.assert_called_once_with(
        notification=notification,
        user_id=user.id,
        task_id=task.id,
        workflow_name=workflow.name,
        author_id=account_owner.id,
        sync=True
    )
    websocket_notification_mock.assert_called_once_with(
        notification=notification,
        user_id=user.id,
        task_id=task.id,
        workflow_name=workflow.name,
        author_id=account_owner.id,
        sync=True
    )


def test_send_resumed_workflow_notification__completed_performer__skip(
    mocker
):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    completed_user = create_test_user(
        is_account_owner=False,
        email="performer@test.test",
        account=account
    )
    TaskPerformer.objects.create(
        task=task,
        user=completed_user,
        is_completed=True,
        date_completed=timezone.now()
    )

    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )

    # act
    _send_resumed_workflow_notification(
        logging=account.log_api_requests,
        task_id=task.id,
        author_id=account_owner.id,
        account_id=account.id,
        workflow_name=workflow.name
    )

    # assert
    assert Notification.objects.filter(
        account_id=account.id,
        type=NotificationType.RESUME_WORKFLOW
    ).count() == 1
    notification = Notification.objects.get(
        task_id=task.id,
        author_id=account_owner.id,
        user_id=account_owner.id,
        account_id=account.id,
        type=NotificationType.RESUME_WORKFLOW,
    )

    send_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        notification=notification,
        method_name=NotificationMethod.resume_workflow,
        user_id=account_owner.id,
        task_id=task.id,
        workflow_name=workflow.name,
        author_id=account_owner.id,
        sync=True
    )


def test_send_resumed_workflow_notification__deleted_performer__skip(
    mocker
):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    user = create_test_user(
        is_account_owner=False,
        email="performer@test.test",
        account=account
    )
    TaskPerformer.objects.create(
        task=task,
        user=user,
        directly_status=DirectlyStatus.DELETED
    )

    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )

    # act
    _send_resumed_workflow_notification(
        logging=account.log_api_requests,
        task_id=task.id,
        author_id=account_owner.id,
        account_id=account.id,
        workflow_name=workflow.name
    )

    # assert
    assert Notification.objects.filter(
        account_id=account.id,
        type=NotificationType.RESUME_WORKFLOW
    ).count() == 1
    notification = Notification.objects.get(
        task_id=task.id,
        author_id=account_owner.id,
        user_id=account_owner.id,
        account_id=account.id,
        type=NotificationType.RESUME_WORKFLOW,
    )

    send_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        notification=notification,
        method_name=NotificationMethod.resume_workflow,
        user_id=account_owner.id,
        task_id=task.id,
        workflow_name=workflow.name,
        author_id=account_owner.id,
        sync=True
    )


def test_send_resumed_workflow_notification__guest_performer__skip(
    mocker
):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    guest = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task=task,
        user=guest,
    )
    TaskPerformer.objects.filter(
        task=task,
        user=account_owner,
    ).update(
        is_completed=True,
        date_completed=timezone.now()
    )

    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )

    # act
    _send_resumed_workflow_notification(
        logging=account.log_api_requests,
        task_id=task.id,
        author_id=account_owner.id,
        account_id=account.id,
        workflow_name=workflow.name
    )

    # assert
    assert Notification.objects.filter(
        account_id=account.id,
        type=NotificationType.RESUME_WORKFLOW
    ).count() == 0
    send_notification_mock.assert_not_called()
