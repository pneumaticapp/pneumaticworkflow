import pytest
from datetime import timedelta
from django.utils import timezone
from pneumatic_backend.processes.enums import DirectlyStatus
from pneumatic_backend.processes.models import TaskPerformer
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_account,
    create_test_guest,
)
from pneumatic_backend.notifications.tasks import (
    _send_due_date_changed
)
from pneumatic_backend.accounts.enums import (
    NotificationType,
    UserType,
)
from pneumatic_backend.accounts.models import Notification
from pneumatic_backend.notifications.services.push import (
    PushNotificationService
)


pytestmark = pytest.mark.django_db


def test_send_due_date_changed__call_services__ok(mocker):

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
    task.due_date = timezone.now() + timedelta(hours=1)
    task.save(update_fields=['due_date'])
    task.performers.add(account_owner)
    push_notification_service_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None
    )
    push_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.push.'
        'PushNotificationService.send_due_date_changed'
    )
    websocket_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.'
        'WebSocketService.send_due_date_changed'
    )

    # act
    _send_due_date_changed(
        logging=account.log_api_requests,
        author_id=account_owner.id,
        task_id=task.id,
        task_name=task.name,
        workflow_name=workflow.name,
        account_id=account.id,
    )

    # assert
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=user.id,
        author_id=account_owner.id,
        account_id=account.id,
        type=NotificationType.DUE_DATE_CHANGED,
    )

    push_kwargs = {
        'user_type': UserType.USER,
        'sync': True,
        'notification': notification,
    }
    push_notification_service_mock.assert_called_once_with(
        logging=account.log_api_requests
    )
    push_notification_mock.assert_called_once_with(
        task_id=task.id,
        task_name=task.name,
        workflow_name=workflow.name,
        user_id=user.id,
        **push_kwargs
    )
    websocket_kwargs = {
        'task_id': task.id,
        'task_name': task.name,
        'workflow_name': workflow.name,
    }
    websocket_notification_mock.assert_called_once_with(
        user_id=user.id,
        user_type=UserType.USER,
        sync=True,
        notification=notification,
        **websocket_kwargs,
    )


def test_send_due_date_changed__completed_performer__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    task.due_date = timezone.now() + timedelta(hours=1)
    task.save(update_fields=['due_date'])
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
    _send_due_date_changed(
        logging=account.log_api_requests,
        author_id=account_owner.id,
        task_id=task.id,
        task_name=task.name,
        workflow_name=workflow.name,
        account_id=account.id,
    )

    # assert
    assert Notification.objects.filter(
        account_id=account.id,
        type=NotificationType.DUE_DATE_CHANGED,
    ).count() == 0
    send_notification_mock.assert_not_called()


def test_send_due_date_changed__deleted_performer__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    task.due_date = timezone.now() + timedelta(hours=1)
    task.save(update_fields=['due_date'])
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
    _send_due_date_changed(
        logging=account.log_api_requests,
        author_id=account_owner.id,
        task_id=task.id,
        task_name=task.name,
        workflow_name=workflow.name,
        account_id=account.id,
    )

    # assert
    assert Notification.objects.filter(
        account_id=account.id,
        type=NotificationType.DUE_DATE_CHANGED,
    ).count() == 0
    send_notification_mock.assert_not_called()


def test_send_due_date_changed__guest_performer__skip(mocker):

    # arrange
    account = create_test_account()
    account_owner = create_test_user(
        is_account_owner=True,
        account=account
    )
    workflow = create_test_workflow(account_owner, tasks_count=1)
    task = workflow.current_task_instance
    task.due_date = timezone.now() + timedelta(hours=1)
    task.save(update_fields=['due_date'])
    guest = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task=task,
        user=guest,
    )
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )

    # act
    _send_due_date_changed(
        logging=account.log_api_requests,
        author_id=account_owner.id,
        task_id=task.id,
        task_name=task.name,
        workflow_name=workflow.name,
        account_id=account.id,
    )

    # assert
    assert Notification.objects.filter(
        account_id=account.id,
        type=NotificationType.DUE_DATE_CHANGED,
    ).count() == 0
    send_notification_mock.assert_not_called()
