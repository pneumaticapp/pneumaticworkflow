from datetime import timedelta

import pytest
from django.conf import settings
from django.utils import timezone

from src.accounts.enums import (
    NotificationType,
)
from src.accounts.models import (
    Notification,
    UserInvite,
)
from src.accounts.serializers.notifications import (
    NotificationTaskSerializer,
    NotificationWorkflowSerializer,
)
from src.notifications.enums import NotificationMethod
from src.notifications.services.email import (
    EmailService,
)
from src.notifications.tasks import (
    _send_unread_notifications,
)
from src.processes.services.events import (
    WorkflowEventService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_user,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_send_unread_notifications__call_all_services__ok(mocker):

    # arrange
    logo_lg = 'https://site.com/logo-lg.jpg'
    account = create_test_account(logo_lg=logo_lg)
    user = create_test_user(account=account)
    user_2 = create_test_user(
        email='t@t.t',
        account=account,
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.performers.add(user_2)
    comment = WorkflowEventService.comment_created_event(
        user=user_2,
        text='Notify',
        task=task,
        after_create_actions=False,
    )
    not_read_timeout_date = (
        timezone.now()
        - timedelta(seconds=settings.UNREAD_NOTIFICATIONS_TIMEOUT)
        - timedelta(minutes=1)
    )
    notification = Notification.objects.create(
        author_id=comment.user_id,
        account_id=comment.user.account_id,
        user=user,
        type=NotificationType.COMMENT,
        text=comment.text,
        task_json=NotificationTaskSerializer(
            instance=comment.task,
            notification_type=NotificationType.COMMENT,
        ).data,
        workflow_json=NotificationWorkflowSerializer(
            instance=comment.task.workflow,
        ).data,
    )
    notification.datetime = not_read_timeout_date
    notification.save(update_fields=['datetime'])
    email_service_init_mock = mocker.patch.object(
        EmailService,
        attribute='__init__',
        return_value=None,
    )
    send_email_mock = mocker.patch(
        'src.notifications.services.email.EmailService'
        '.send_unread_notifications',
    )

    # act
    _send_unread_notifications()

    # assert
    notification.refresh_from_db()
    assert notification.is_notified_about_not_read is True
    email_service_init_mock.assert_called_once_with(
        logo_lg=account.logo_lg,
        account_id=account.id,
        logging=account.log_api_requests,
    )
    link = (
        'http://localhost'
        '?utm_source=notifications&utm_campaign=unread_notifications'
    )
    send_email_mock.assert_called_once_with(
        user_id=user.id,
        user_first_name=user.first_name,
        user_email=user.email,
        link=link,
    )


def test_send_unread_notifications__second_mailing__not_sent(mocker):

    # arrange
    logo_lg = 'https://site.com/logo-lg.jpg'
    account = create_test_account(logo_lg=logo_lg)
    user = create_test_user(account=account)
    user_2 = create_test_user(
        email='t@t.t',
        account=account,
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.performers.add(user_2)
    comment = WorkflowEventService.comment_created_event(
        user=user_2,
        text='Notify',
        task=task,
        after_create_actions=False,
    )

    not_read_timeout_date = (
        timezone.now()
        - timedelta(seconds=settings.UNREAD_NOTIFICATIONS_TIMEOUT)
        - timedelta(minutes=1)
    )
    notification = Notification.objects.create(
        author_id=comment.user_id,
        account_id=comment.user.account_id,
        user=user,
        type=NotificationType.COMMENT,
        text=comment.text,
        task_json=NotificationTaskSerializer(
            instance=comment.task,
            notification_type=NotificationType.COMMENT,
        ).data,
        workflow_json=NotificationWorkflowSerializer(
            instance=comment.task.workflow,
        ).data,
    )
    notification.datetime = not_read_timeout_date
    notification.save(update_fields=['datetime'])
    _send_unread_notifications()
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_unread_notifications()

    # assert
    notification.refresh_from_db()
    assert notification.is_notified_about_not_read is True
    send_notification_mock.assert_not_called()


def test_send_unread_notifications__not_read_timeout__not_sent(mocker):

    # arrange
    logo_lg = 'https://site.com/logo-lg.jpg'
    account = create_test_account(logo_lg=logo_lg)
    user = create_test_user(account=account)
    user_2 = create_test_user(
        email='t@t.t',
        account=account,
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.performers.add(user_2)
    comment = WorkflowEventService.comment_created_event(
        user=user_2,
        text='Notify',
        task=task,
        after_create_actions=False,
    )
    not_read_timeout_date = (
        timezone.now()
        - timedelta(seconds=settings.UNREAD_NOTIFICATIONS_TIMEOUT)
        + timedelta(minutes=1)
    )
    notification = Notification.objects.create(
        author_id=comment.user_id,
        account_id=comment.user.account_id,
        user=user,
        type=NotificationType.COMMENT,
        text=comment.text,
        task_json=NotificationTaskSerializer(
            instance=comment.task,
            notification_type=NotificationType.COMMENT,
        ).data,
        workflow_json=NotificationWorkflowSerializer(
            instance=comment.task.workflow,
        ).data,
    )
    notification.datetime = not_read_timeout_date
    notification.save(update_fields=['datetime'])
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_unread_notifications()

    # assert
    notification.refresh_from_db()
    assert notification.is_notified_about_not_read is False
    send_notification_mock.assert_not_called()


def test_send_unread_notifications__deleted__not_sent(mocker):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(
        email='t@t.t',
        account=user.account,
    )

    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.performers.add(user_2)
    comment = WorkflowEventService.comment_created_event(
        user=user_2,
        text='Notify',
        task=task,
        after_create_actions=False,
    )
    not_read_timeout_date = (
        timezone.now()
        - timedelta(seconds=settings.UNREAD_NOTIFICATIONS_TIMEOUT)
        - timedelta(minutes=1)
    )
    notification = Notification.objects.create(
        author_id=comment.user_id,
        account_id=comment.user.account_id,
        user=user,
        type=NotificationType.COMMENT,
        text=comment.text,
        task_json=NotificationTaskSerializer(
            instance=comment.task,
            notification_type=NotificationType.COMMENT,
        ).data,
        workflow_json=NotificationWorkflowSerializer(
            instance=comment.task.workflow,
        ).data,
    )
    notification.datetime = not_read_timeout_date
    notification.save(update_fields=['datetime'])
    notification.delete()
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_unread_notifications()

    # assert
    notification.refresh_from_db()
    assert notification.is_notified_about_not_read is False
    send_notification_mock.assert_not_called()


def test_send_unread_notifications__not_subscriber__not_sent(mocker):

    # arrange
    user = create_test_user()
    user.is_comments_mentions_subscriber = False
    user.save(update_fields=['is_comments_mentions_subscriber'])
    user_2 = create_test_user(
        email='t@t.t',
        account=user.account,
    )

    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.performers.add(user_2)
    comment = WorkflowEventService.comment_created_event(
        user=user_2,
        text='Notify',
        task=task,
        after_create_actions=False,
    )
    not_read_timeout_date = (
        timezone.now()
        - timedelta(seconds=settings.UNREAD_NOTIFICATIONS_TIMEOUT)
        - timedelta(minutes=1)
    )
    notification = Notification.objects.create(
        author_id=comment.user_id,
        account_id=comment.user.account_id,
        user=user,
        type=NotificationType.COMMENT,
        text=comment.text,
        task_json=NotificationTaskSerializer(
            instance=comment.task,
            notification_type=NotificationType.COMMENT,
        ).data,
        workflow_json=NotificationWorkflowSerializer(
            instance=comment.task.workflow,
        ).data,
    )
    notification.datetime = not_read_timeout_date
    notification.save(update_fields=['datetime'])
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )

    # act
    _send_unread_notifications()

    # assert
    notification.refresh_from_db()
    assert notification.is_notified_about_not_read is False
    send_notification_mock.assert_not_called()


def test_send_unread_notifications__owner_invited_in_another_acc__ok(mocker):

    # arrange
    account = create_test_account(
        logo_lg='https://logo.jpg',
        log_api_requests=True,
    )
    account_owner = create_test_user(
        account=account,
        email='account_owner@test.test',
    )
    user = create_test_user(
        account=account,
        email='user@test.test',
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.performers.add(user)
    notification = Notification.objects.create(
        author=user,
        account=account,
        user=account_owner,
        type=NotificationType.URGENT,
        task_json=NotificationTaskSerializer(
            instance=task,
            notification_type=NotificationType.URGENT,
        ).data,
        workflow_json=NotificationWorkflowSerializer(
            instance=workflow,
        ).data,
    )
    not_read_timeout_date = (
        timezone.now()
        - timedelta(seconds=settings.UNREAD_NOTIFICATIONS_TIMEOUT)
        - timedelta(minutes=1)
    )
    notification.datetime = not_read_timeout_date
    notification.save(update_fields=['datetime'])
    send_notification_mock = mocker.patch(
        'src.notifications.tasks._send_notification',
    )
    another_account = create_test_account()
    UserInvite.objects.create(
        email=account_owner.email,
        account=another_account,
        invited_user=account_owner,
    )

    # act
    _send_unread_notifications()

    # assert
    notification.refresh_from_db()
    assert notification.is_notified_about_not_read is True
    link = (
        'http://localhost'
        '?utm_source=notifications&utm_campaign=unread_notifications'
    )
    send_notification_mock.assert_called_once_with(
        logging=account.log_api_requests,
        method_name=NotificationMethod.unread_notifications,
        user_id=account_owner.id,
        user_first_name=account_owner.first_name,
        user_email=account_owner.email,
        logo_lg=account.logo_lg,
        account_id=account.id,
        link=link,
    )
