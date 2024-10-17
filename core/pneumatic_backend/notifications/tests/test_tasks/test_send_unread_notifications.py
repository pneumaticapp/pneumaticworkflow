import pytest
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
    create_test_user,
    create_test_account,
)
from pneumatic_backend.notifications.tasks import (
    _send_unread_notifications
)
from pneumatic_backend.notifications.enums import NotificationMethod
from pneumatic_backend.accounts.enums import (
    NotificationType,
)
from pneumatic_backend.accounts.models import (
    Notification,
    UserInvite,
)
from pneumatic_backend.processes.api_v2.services.events import (
    WorkflowEventService
)
pytestmark = pytest.mark.django_db


def test_send_unread_notifications__end_to_end__ok(mocker):

    # arrange
    logo_lg = 'https://site.com/logo-lg.jpg'
    account = create_test_account(logo_lg=logo_lg)
    user = create_test_user(account=account)
    user_2 = create_test_user(
        email='t@t.t',
        account=account
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(user_2)
    comment = WorkflowEventService.comment_created_event(
        user=user_2,
        text='Notify',
        workflow=workflow,
        after_create_actions=False
    )
    not_read_timeout_date = (
        timezone.now()
        - settings.NOTIFICATIONS_NOT_READ_TIMEOUT
        - timedelta(minutes=1)
    )
    notification = Notification.objects.create(
        author_id=comment.user_id,
        account_id=comment.user.account_id,
        user=user,
        type=NotificationType.COMMENT,
        text=comment.text,
        task=comment.task,
    )
    notification.datetime = not_read_timeout_date
    notification.save(update_fields=['datetime'])
    send_email_mock = mocker.patch(
        'pneumatic_backend.notifications.services.email.EmailService'
        '.send_unread_notifications'
    )

    # act
    _send_unread_notifications()

    # assert
    notification.refresh_from_db()
    assert notification.is_notified_about_not_read is True
    send_email_mock.assert_called_once_with(
        user_id=user.id,
        user_first_name=user.first_name,
        user_email=user.email,
        logo_lg=account.logo_lg,
    )


def test_send_unread_notifications__second_mailing__not_sent(mocker):

    # arrange
    logo_lg = 'https://site.com/logo-lg.jpg'
    account = create_test_account(logo_lg=logo_lg)
    user = create_test_user(account=account)
    user_2 = create_test_user(
        email='t@t.t',
        account=account
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(user_2)
    comment = WorkflowEventService.comment_created_event(
        user=user_2,
        text='Notify',
        workflow=workflow,
    )

    not_read_timeout_date = (
        timezone.now()
        - settings.NOTIFICATIONS_NOT_READ_TIMEOUT
        - timedelta(minutes=1)
    )
    notification = Notification.objects.create(
        author_id=comment.user_id,
        account_id=comment.user.account_id,
        user=user,
        type=NotificationType.COMMENT,
        task=comment.task,
    )
    notification.datetime = not_read_timeout_date
    notification.save(update_fields=['datetime'])
    _send_unread_notifications()
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
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
        account=account
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(user_2)
    comment = WorkflowEventService.comment_created_event(
        user=user_2,
        text='Notify',
        workflow=workflow,
    )
    not_read_timeout_date = (
        timezone.now()
        - settings.NOTIFICATIONS_NOT_READ_TIMEOUT
        + timedelta(minutes=1)
    )
    notification = Notification.objects.create(
        author_id=comment.user_id,
        account_id=comment.user.account_id,
        user=user,
        type=NotificationType.COMMENT,
        text=comment.text,
        task=comment.task,
    )
    notification.datetime = not_read_timeout_date
    notification.save(update_fields=['datetime'])
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
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
        account=user.account
    )

    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(user_2)
    comment = WorkflowEventService.comment_created_event(
        user=user_2,
        text='Notify',
        workflow=workflow,
    )
    not_read_timeout_date = (
        timezone.now()
        - settings.NOTIFICATIONS_NOT_READ_TIMEOUT
        - timedelta(minutes=1)
    )
    notification = Notification.objects.create(
        author_id=comment.user_id,
        account_id=comment.user.account_id,
        user=user,
        type=NotificationType.COMMENT,
        text=comment.text,
        task=comment.task,
    )
    notification.datetime = not_read_timeout_date
    notification.save(update_fields=['datetime'])
    notification.delete()
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
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
        account=user.account
    )

    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(user_2)
    comment = WorkflowEventService.comment_created_event(
        user=user_2,
        text='Notify',
        workflow=workflow,
    )
    not_read_timeout_date = (
        timezone.now()
        - settings.NOTIFICATIONS_NOT_READ_TIMEOUT
        - timedelta(minutes=1)
    )
    notification = Notification.objects.create(
        author_id=comment.user_id,
        account_id=comment.user.account_id,
        user=user,
        type=NotificationType.COMMENT,
        text=comment.text,
        task=comment.task,
    )
    notification.datetime = not_read_timeout_date
    notification.save(update_fields=['datetime'])
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )

    # act
    _send_unread_notifications()

    # assert
    notification.refresh_from_db()
    assert notification.is_notified_about_not_read is False
    send_notification_mock.assert_not_called()


def test_send_unread_notifications__owner_invited_in_another_acc__ok(mocker):

    # arrange
    account_owner = create_test_user(
        email='account_owner@test.test',
    )
    user = create_test_user(
        email='user@test.test',
        account=account_owner.account
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(user)
    notification = Notification.objects.create(
        author=user,
        account=user.account,
        user=account_owner,
        type=NotificationType.URGENT,
        task=task,
    )
    not_read_timeout_date = (
        timezone.now()
        - settings.NOTIFICATIONS_NOT_READ_TIMEOUT
        - timedelta(minutes=1)
    )
    notification.datetime = not_read_timeout_date
    notification.save(update_fields=['datetime'])
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
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
    send_notification_mock.assert_called_once_with(
        method_name=NotificationMethod.unread_notifications,
        user_id=account_owner.id,
        user_first_name=account_owner.first_name,
        user_email=account_owner.email,
        logo_lg=None,
    )


def test_send_unread_notifications__payment_card_not_provided__not_sent(
    mocker
):

    # arrange
    account = create_test_account(
        payment_card_provided=False
    )
    user = create_test_user(account=account)
    user_2 = create_test_user(
        email='t@t.t',
        account=user.account
    )

    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.current_task_instance
    task.performers.add(user_2)
    comment = WorkflowEventService.comment_created_event(
        user=user_2,
        text='Notify',
        workflow=workflow,
    )
    not_read_timeout_date = (
        timezone.now()
        - settings.NOTIFICATIONS_NOT_READ_TIMEOUT
        - timedelta(minutes=1)
    )
    notification = Notification.objects.create(
        author_id=comment.user_id,
        account_id=comment.user.account_id,
        user=user,
        type=NotificationType.COMMENT,
        text=comment.text,
        task=comment.task,
    )
    notification.datetime = not_read_timeout_date
    notification.save(update_fields=['datetime'])
    send_notification_mock = mocker.patch(
        'pneumatic_backend.notifications.tasks._send_notification'
    )

    # act
    _send_unread_notifications()

    # assert
    notification.refresh_from_db()
    send_notification_mock.assert_not_called()
