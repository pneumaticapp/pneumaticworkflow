from datetime import timedelta

import pytest
from django.utils import timezone

from src.accounts.enums import (
    NotificationStatus,
    NotificationType,
)
from src.accounts.models import Notification
from src.accounts.serializers.notifications import (
    NotificationTaskSerializer,
    NotificationWorkflowSerializer,
)
from src.notifications.enums import NotificationMethod
from src.notifications.services.push import (
    PushNotificationService,
)
from src.notifications.tasks import (
    _send_overdue_task_notification,
)
from src.processes.enums import (
    DirectlyStatus,
    WorkflowStatus,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_user,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_send_overdue_task_notification__call_all_services__ok(mocker):

    # arrange
    logo_lg = 'https://site.com/logo-lg.jpg'
    account = create_test_account(logo_lg=logo_lg, log_api_requests=True)
    user = create_test_user(account=account)
    workflow = create_test_workflow(user, tasks_count=2)
    task = workflow.tasks.get(number=1)
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    send_email_mock = mocker.patch(
        'src.notifications.services.email.EmailService'
        '.send_overdue_task',
    )
    send_ws_mock = mocker.patch(
        'src.notifications.services.websockets.WebSocketService'
        '.send_overdue_task',
    )
    push_notification_service_init_mock = mocker.patch.object(
        PushNotificationService,
        attribute='__init__',
        return_value=None,
    )
    send_push_mock = mocker.patch(
        'src.notifications.services.push.'
        'PushNotificationService.send_overdue_task',
    )

    # act
    _send_overdue_task_notification()

    # assert
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        status=NotificationStatus.NEW,
    )
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
        token=None,
        notification=notification,
        sync=True,
    )

    send_ws_mock.assert_called_once_with(
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
        token=None,
        notification=notification,
        sync=True,
    )
    push_notification_service_init_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    send_push_mock.assert_called_once_with(
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
        token=None,
        notification=notification,
        sync=True,
    )


def test_send_overdue_task_notification__already_sent__not_sent(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task = workflow.tasks.get(number=1)
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )
    notification = Notification.objects.create(
        task_id=task.id,
        task_json=NotificationTaskSerializer(
            instance=task,
            notification_type=NotificationType.OVERDUE_TASK,
        ).data,
        workflow_json=NotificationWorkflowSerializer(
            instance=task.workflow,
        ).data,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user.account.id,
    )

    # act
    _send_overdue_task_notification()

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user.account.id,
    ).exclude(id=notification.id).exists()
    send_notification_mock.assert_not_called()


def test_send_overdue_task_notification__guest__ok(mocker):

    # arrange
    account = create_test_account(
        logo_lg='https://logo.jpg',
        log_api_requests=True,
    )
    user = create_test_user(account=account)
    workflow = create_test_workflow(user, tasks_count=2)
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    guest = create_test_guest(account=account, email='t@t.t')
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )
    token = '1!@#23!3'
    get_token_mock = mocker.patch(
        'src.authentication.services.guest_auth.GuestJWTAuthService.'
        'get_str_token',
        return_value=token,
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
        logging=account.log_api_requests,
        method_name=NotificationMethod.overdue_task,
        account_id=guest.account_id,
        user_id=guest.id,
        user_type=guest.type,
        user_email=guest.email,
        logo_lg=account.logo_lg,
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
        token=token,
    )
    get_token_mock.assert_called_once_with(
        task_id=task.id,
        user_id=guest.id,
        account_id=user.account.id,
    )


def test_send_overdue_task_notification__guest_already_sent__not_sent(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    guest = create_test_guest(account=user.account, email='t@t.t')
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )
    notification = Notification.objects.create(
        task_id=task.id,
        task_json=NotificationTaskSerializer(
            instance=task,
            notification_type=NotificationType.OVERDUE_TASK,
        ).data,
        workflow_json=NotificationWorkflowSerializer(
            instance=task.workflow,
        ).data,
        user_id=guest.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=guest.account.id,
    )

    # act
    _send_overdue_task_notification()

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user.account.id,
    ).exclude(id=notification.id).exists()
    send_notification_mock.assert_not_called()


def test_send_overdue_task_notification__not_overdue__skip(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task = workflow.tasks.get(number=1)
    task.due_date = timezone.now() + timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_overdue_task_notification()

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user.account.id,
    ).exists()
    send_notification_mock.assert_not_called()


def test_send_overdue_task_notification__two_performers__ok(mocker):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(
        is_account_owner=False,
        account=user.account,
        email='t@t.t',
    )
    workflow = create_test_workflow(user, tasks_count=2)
    task = workflow.tasks.get(number=1)
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    task.add_raw_performer(user_2)
    task.update_performers()
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_overdue_task_notification()

    # assert
    notification_1 = Notification.objects.get(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        status=NotificationStatus.NEW,
    )
    notification_2 = Notification.objects.get(
        task_id=task.id,
        user_id=user_2.id,
        type=NotificationType.OVERDUE_TASK,
        status=NotificationStatus.NEW,
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
        ),
    ])


def test_send_overdue_task_notification__completed_task__skip(
    mocker,
    api_client,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2)
    task = workflow.tasks.get(number=1)
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    TaskPerformer.objects.filter(user_id=user.id).update(is_completed=True)

    mocker.patch(
        'src.notifications.tasks._send_notification',
    )
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    api_client.token_authenticate(user)

    # act
    _send_overdue_task_notification()

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user.account.id,
    ).exists()
    send_notification_mock.assert_not_called()


def test_send_overdue_task_notification__terminated_workflow__skip(
    mocker,
    api_client,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user, tasks_count=2, finalizable=True)
    task = workflow.tasks.get(number=1)
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    api_client.token_authenticate(user)
    response = api_client.delete(f'/workflows/{workflow.id}')
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_overdue_task_notification()

    # assert
    assert response.status_code == 204
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user.account.id,
    ).exists()
    send_notification_mock.assert_not_called()


def test_send_overdue_task_notification__ended__workflow__skip(
    mocker,
    api_client,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
        finalizable=True,
        status=WorkflowStatus.DONE,
    )
    task = workflow.tasks.get(number=1)
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    api_client.token_authenticate(user)
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_overdue_task_notification()

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user.account.id,
    ).exists()
    send_notification_mock.assert_not_called()
    assert workflow.status == WorkflowStatus.DONE


def test_send_overdue_task_notification__delayed_workflow__skip(
    mocker,
    api_client,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(
        user=user,
        tasks_count=2,
        finalizable=True,
    )
    workflow.status = WorkflowStatus.DELAYED
    workflow.save(update_fields=['status'])
    task = workflow.tasks.get(number=1)
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    api_client.token_authenticate(user)
    workflow.refresh_from_db()
    mocker.patch(
        'src.notifications.tasks'
        '.send_new_task_notification.delay',
    )
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_overdue_task_notification()

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user.account.id,
    ).exists()
    send_notification_mock.assert_not_called()


def test_send_overdue_task_notification__deleted_performer__skip(mocker):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(
        is_account_owner=False,
        account=user.account,
        email='t@t.t',
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    TaskPerformer.objects.create(
        task=task,
        user=user_2,
        directly_status=DirectlyStatus.DELETED,
    )
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_overdue_task_notification()

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user_2.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user_2.account.id,
    ).exists()
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        status=NotificationStatus.NEW,
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


def test_send_overdue_task_notification__completed_performer__skip(mocker):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(
        is_account_owner=False,
        account=user.account,
        email='t@t.t',
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.due_date = timezone.now() - timedelta(minutes=5)
    task.save(update_fields=['due_date'])
    TaskPerformer.objects.create(
        task=task,
        user=user_2,
        is_completed=True,
        date_completed=timezone.now(),
    )
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_overdue_task_notification()

    # assert
    assert not Notification.objects.filter(
        task_id=task.id,
        user_id=user_2.id,
        type=NotificationType.OVERDUE_TASK,
        account_id=user_2.account.id,
    ).exists()
    notification = Notification.objects.get(
        task_id=task.id,
        user_id=user.id,
        type=NotificationType.OVERDUE_TASK,
        status=NotificationStatus.NEW,
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
