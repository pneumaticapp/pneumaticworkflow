import pytest
from datetime import timedelta
from django.utils import timezone
from django.db import connection
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_guest,
    create_test_account,
)
from pneumatic_backend.notifications.services.push import (
    PushNotificationService
)
from pneumatic_backend.processes.models.workflows.task import TaskPerformer
from pneumatic_backend.notifications.tasks import (
    _send_overdue_task_notification
)
from pneumatic_backend.notifications.enums import NotificationMethod
from pneumatic_backend.accounts.enums import (
    NotificationType,
    NotificationStatus
)
from pneumatic_backend.accounts.models import Notification
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    DirectlyStatus,
)

pytestmark = pytest.mark.django_db


def test_send_overdue_task_notification__end_to_end__ok(mocker):

    # arrange
    logo_lg = 'https://site.com/logo-lg.jpg'
    account = create_test_account(logo_lg=logo_lg, log_api_requests=True)
    user = create_test_user(account=account)
    workflow = create_test_workflow(user, tasks_count=2)
    task = workflow.current_task_instance
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    send_email_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.EmailService'
        '.send_overdue_task'
    )
    send_ws_mock = mocker.patch(
        'pneumatic_backend.notifications.services.websockets.WebSocketService'
        '.send_overdue_task'
    )
    push_notification_service_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None
    )
    send_push_mock = mocker.patch(
        'pneumatic_backend.notifications.services.push.'
        'PushNotificationService.send_overdue_task'
    )
    mocker.patch(
        'pneumatic_backend.executor.connections',
        new={'replica': connection}
    )

    # act
    _send_overdue_task_notification()

    # assert
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        status=NotificationStatus.NEW
    )
    email_kwargs = {
        'account_id': user.account_id,
        'notification': notification,
        'sync': True,
    }
    send_email_mock.assert_called_once_with(
        user_id=user.id,
        user_email=user.email,
        user_type=user.type,
        workflow_id=workflow.id,
        workflow_name=workflow.name,
        task_id=task.id,
        task_name=task.name,
        template_name=workflow.template.name,
        workflow_starter_id=workflow.workflow_starter_id,
        workflow_starter_first_name=user.first_name,
        workflow_starter_last_name=user.last_name,
        logo_lg=logo_lg,
        token=None,
        **email_kwargs
    )
    ws_kwargs = {
        'account_id': user.account_id,
        'logo_lg': logo_lg,
        'user_email': user.email,
        'task_id': task.id,
        'task_name': task.name,
        'template_name': workflow.template.name,
        'workflow_id': workflow.id,
        'workflow_name': workflow.name,
        'workflow_starter_id': workflow.workflow_starter_id,
        'workflow_starter_first_name': user.first_name,
        'workflow_starter_last_name': user.last_name,
        'token': None,
    }
    send_ws_mock.assert_called_once_with(
        user_id=user.id,
        user_type=user.type,
        notification=notification,
        sync=True,
        **ws_kwargs
    )
    push_notification_service_mock.assert_called_once_with(
        logging=account.log_api_requests,
    )
    push_kwargs = {
        'account_id': user.account_id,
        'logo_lg': logo_lg,
        'user_email': user.email,
        'workflow_id': workflow.id,
        'template_name': workflow.template.name,
        'workflow_starter_id': workflow.workflow_starter_id,
        'workflow_starter_first_name': user.first_name,
        'workflow_starter_last_name': user.last_name,
        'notification': notification,
        'sync': True,
        'token': None,
    }
    send_push_mock.assert_called_once_with(
        user_id=user.id,
        user_type=user.type,
        task_id=task.id,
        task_name=task.name,
        workflow_name=workflow.name,
        **push_kwargs
    )


def test_send_overdue_task_notification__already_sent__not_sent(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task = workflow.current_task_instance
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )
    mocker.patch(
        'pneumatic_backend.executor.connections',
        new={'replica': connection}
    )
    notification = Notification.objects.create(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user.account.id
    )

    # act
    _send_overdue_task_notification()

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user.account.id
    ).exclude(id=notification.id).exists()
    send_notification_mock.assert_not_called()


def test_send_overdue_task_notification__guest__ok(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task = workflow.current_task_instance
    task.taskperformer_set.all().delete()
    guest = create_test_guest(account=user.account, email='t@t.t')
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id
    )
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )
    token = '1!@#23!3'
    get_token_mock = mocker.patch(
        'pneumatic_backend.authentication.services.GuestJWTAuthService.'
        'get_str_token',
        return_value=token
    )
    mocker.patch(
        'pneumatic_backend.executor.connections',
        new={'replica': connection}
    )

    # act
    _send_overdue_task_notification()

    # assert
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=guest.id,
        type=NotificationType.OVERDUE_TASK,
    )
    send_notification_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        method_name=NotificationMethod.overdue_task,
        account_id=guest.account_id,
        user_id=guest.id,
        user_type=guest.type,
        user_email=guest.email,
        logo_lg=None,
        task_id=task.id,
        task_name=task.name,
        workflow_id=workflow.id,
        workflow_name=workflow.name,
        template_name=workflow.template.name,
        workflow_starter_id=workflow.workflow_starter_id,
        workflow_starter_first_name=user.first_name,
        workflow_starter_last_name=user.last_name,
        notification=notification,
        sync=True,
        token=token
    )
    get_token_mock.assert_called_once_with(
        task_id=task.id,
        user_id=guest.id,
        account_id=user.account.id
    )


def test_send_overdue_task_notification__guest_already_sent__not_sent(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task = workflow.current_task_instance
    task.taskperformer_set.all().delete()
    guest = create_test_guest(account=user.account, email='t@t.t')
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id
    )
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )
    mocker.patch(
        'pneumatic_backend.executor.connections',
        new={'replica': connection}
    )
    notification = Notification.objects.create(
        task_id=task.id,
        user_id=guest.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=guest.account.id
    )

    # act
    _send_overdue_task_notification()

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user.account.id
    ).exclude(id=notification.id).exists()
    send_notification_mock.assert_not_called()


def test_send_overdue_task_notification__not_overdue__skip(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task = workflow.current_task_instance
    task.due_date = timezone.now() + timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )
    mocker.patch(
        'pneumatic_backend.executor.connections',
        new={'replica': connection}
    )

    # act
    _send_overdue_task_notification()

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user.account.id
    ).exists()
    send_notification_mock.assert_not_called()


def test_send_overdue_task_notification__two_performers__ok(mocker):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(
        is_account_owner=False,
        account=user.account,
        email='t@t.t'
    )
    workflow = create_test_workflow(user, tasks_count=2)
    task = workflow.current_task_instance
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    task.add_raw_performer(user_2)
    task.update_performers()
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )
    mocker.patch(
        'pneumatic_backend.executor.connections',
        new={'replica': connection}
    )

    # act
    _send_overdue_task_notification()

    # assert
    notification_1 = Notification.objects.get(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        status=NotificationStatus.NEW
    )
    notification_2 = Notification.objects.get(
        task_id=task.id,
        user_id=user_2.id,
        type=NotificationType.OVERDUE_TASK,
        status=NotificationStatus.NEW
    )
    assert send_notification_mock.call_count == 2
    send_notification_mock.has_calls([
        mocker.call(
            logging=user.account.log_api_requests,
            method_name=NotificationMethod.overdue_task,
            account_id=user.account_id,
            user_id=user.id,
            user_type=user.type,
            user_email=user.email,
            logo_lg=None,
            task_id=task.id,
            task_name=task.name,
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            template_name=workflow.template.name,
            workflow_starter_id=workflow.workflow_starter_id,
            workflow_starter_first_name=user.first_name,
            workflow_starter_last_name=user.last_name,
            notification=notification_1,
        ),
        mocker.call(
            logging=user_2.account.log_api_requests,
            method_name=NotificationMethod.overdue_task,
            account_id=user.account_id,
            user_id=user_2.id,
            user_type=user.type,
            user_email=user_2.email,
            logo_lg=None,
            task_id=task.id,
            task_name=task.name,
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            template_name=workflow.template.name,
            workflow_starter_id=workflow.workflow_starter_id,
            workflow_starter_first_name=user.first_name,
            workflow_starter_last_name=user.last_name,
            notification=notification_2,
        )
    ])


def test_send_overdue_task_notification__completed_task__skip(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task = workflow.current_task_instance
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])

    mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )
    mocker.patch(
        'pneumatic_backend.executor.connections',
        new={'replica': connection}
    )
    mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_new_task_notification'
    )

    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': task.id}
    )
    workflow.refresh_from_db()

    # act
    _send_overdue_task_notification()

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user.account.id
    ).exists()


def test_send_overdue_task_notification__terminated_workflow__skip(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2, finalizable=True)
    task = workflow.current_task_instance
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    api_client.token_authenticate(user)
    response = api_client.delete(f'/workflows/{workflow.id}')
    mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_new_task_notification'
    )
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )
    mocker.patch(
        'pneumatic_backend.executor.connections',
        new={'replica': connection}
    )

    # act
    _send_overdue_task_notification()

    # assert
    assert response.status_code == 204
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user.account.id
    ).exists()
    send_notification_mock.assert_not_called()


def test_send_overdue_task_notification__ended__workflow__skip(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2, finalizable=True)
    task = workflow.current_task_instance
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    api_client.token_authenticate(user)
    response = api_client.post(f'/workflows/{workflow.id}/finish')
    workflow.refresh_from_db()
    mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_new_task_notification'
    )
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )
    mocker.patch(
        'pneumatic_backend.executor.connections',
        new={'replica': connection}
    )

    # act
    _send_overdue_task_notification()

    # assert
    assert response.status_code == 204
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user.account.id
    ).exists()
    send_notification_mock.assert_not_called()
    assert workflow.status == WorkflowStatus.DONE


def test_send_overdue_task_notification__delayed_workflow__skip(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
        finalizable=True
    )
    workflow.status = WorkflowStatus.DELAYED
    workflow.save(update_fields=['status'])
    task = workflow.current_task_instance
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    api_client.token_authenticate(user)
    workflow.refresh_from_db()
    mocker.patch(
        'pneumatic_backend.processes.services.websocket.WSSender.'
        'send_new_task_notification'
    )
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )
    mocker.patch(
        'pneumatic_backend.executor.connections',
        new={'replica': connection}
    )

    # act
    _send_overdue_task_notification()

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user.account.id
    ).exists()
    send_notification_mock.assert_not_called()


def test_send_overdue_task_notification__deleted_performer__skip(mocker):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(
        is_account_owner=False,
        account=user.account,
        email='t@t.t'
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    TaskPerformer.objects.create(
        task=task,
        user=user_2,
        directly_status=DirectlyStatus.DELETED
    )
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )
    mocker.patch(
        'pneumatic_backend.executor.connections',
        new={'replica': connection}
    )

    # act
    _send_overdue_task_notification()

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user_2.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user_2.account.id
    ).exists()
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        status=NotificationStatus.NEW
    )
    send_notification_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        method_name=NotificationMethod.overdue_task,
        account_id=user.account_id,
        user_id=user.id,
        user_type=user.type,
        user_email=user.email,
        logo_lg=None,
        task_id=task.id,
        task_name=task.name,
        workflow_id=workflow.id,
        workflow_name=workflow.name,
        template_name=workflow.template.name,
        workflow_starter_id=workflow.workflow_starter_id,
        workflow_starter_first_name=user.first_name,
        workflow_starter_last_name=user.last_name,
        notification=notification,
        sync=True,
        token=None
    )


def test_send_overdue_task_notification__completed_performer__skip(mocker):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(
        is_account_owner=False,
        account=user.account,
        email='t@t.t'
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    TaskPerformer.objects.create(
        task=task,
        user=user_2,
        is_completed=True,
        date_completed=timezone.now()
    )
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )
    mocker.patch(
        'pneumatic_backend.executor.connections',
        new={'replica': connection}
    )

    # act
    _send_overdue_task_notification()

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user_2.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user_2.account.id
    ).exists()
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        status=NotificationStatus.NEW
    )
    send_notification_mock.assert_called_once_with(
        logging=user.account.log_api_requests,
        method_name=NotificationMethod.overdue_task,
        account_id=user.account_id,
        user_id=user.id,
        user_type=user.type,
        user_email=user.email,
        logo_lg=None,
        task_id=task.id,
        task_name=task.name,
        workflow_id=workflow.id,
        workflow_name=workflow.name,
        template_name=workflow.template.name,
        workflow_starter_id=workflow.workflow_starter_id,
        workflow_starter_first_name=user.first_name,
        workflow_starter_last_name=user.last_name,
        notification=notification,
        sync=True,
        token=None,
    )
