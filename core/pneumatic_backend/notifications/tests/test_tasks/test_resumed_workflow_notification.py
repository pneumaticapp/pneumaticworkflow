import pytest
from django.utils import timezone
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_account,
    create_test_guest,
    create_test_group
)
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.notifications.tasks import (
    _send_resumed_workflow_notification
)
from pneumatic_backend.accounts.enums import (
    NotificationType,
)
from pneumatic_backend.accounts.models import Notification
from pneumatic_backend.processes.models import TaskPerformer
from pneumatic_backend.processes.enums import (
    DirectlyStatus,
    PerformerType,
)
from pneumatic_backend.notifications.enums import (
    NotificationMethod,
)
from pneumatic_backend.notifications.services.push import (
    PushNotificationService
)


pytestmark = pytest.mark.django_db


def test_send_resumed_workflow_notification__call_services__ok(mocker):

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
        author_id=account_owner.id,
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
        type=NotificationType.RESUME_WORKFLOW,
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
        sync=True
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


def test_send_resumed_workflow_notification__call_services_with_group__ok(
    mocker
):

    # arrange
    account = create_test_account(
        log_api_requests=True,
        logo_lg='https://logo.jpg',
        plan=BillingPlanType.PREMIUM
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
    user_in_group = create_test_user(
        email='t2@t.t',
        account=account,
        is_account_owner=False
    )
    group = create_test_group(user.account, users=[user_in_group])
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.remove(user)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.CREATED
    )
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
        author_id=account_owner.id,
        account_id=account.id,
        task_id=task.id,
        logo_lg=account.logo_lg,
    )

    # assert
    notification = Notification.objects.get(
        task_id=task.id,
        author_id=account_owner.id,
        user_id=user_in_group.id,
        account_id=account.id,
        type=NotificationType.RESUME_WORKFLOW,
    )
    push_notification_service_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    push_notification_mock.assert_called_once_with(
        notification=notification,
        user_id=user_in_group.id,
        user_email=user_in_group.email,
        task_id=task.id,
        workflow_name=workflow.name,
        author_id=account_owner.id,
        sync=True
    )
    websocket_notification_mock.assert_called_once_with(
        notification=notification,
        user_id=user_in_group.id,
        user_email=user_in_group.email,
        task_id=task.id,
        workflow_name=workflow.name,
        author_id=account_owner.id,
        sync=True
    )


def test_send_resumed_workflow_notification__completed_performer__skip(
    mocker
):

    # arrange
    account = create_test_account(logo_lg='https://logo.jpg')
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
        author_id=account_owner.id,
        account_id=account.id,
        task_id=task.id,
        logo_lg=account.logo_lg,
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
        user_email=account_owner.email,
        account_id=account.id,
        logo_lg=account.logo_lg,
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
        author_id=account_owner.id,
        account_id=account.id,
        task_id=task.id,
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
        user_email=account_owner.email,
        account_id=account.id,
        logo_lg=account.logo_lg,
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
        author_id=account_owner.id,
        account_id=account.id,
        task_id=task.id,
        logo_lg=account.logo_lg,
    )

    # assert
    assert Notification.objects.filter(
        account_id=account.id,
        type=NotificationType.RESUME_WORKFLOW
    ).count() == 0
    send_notification_mock.assert_not_called()
