from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import pytz
from celery import shared_task
from celery.task import Task as TaskCelery
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from firebase_admin.exceptions import FirebaseError

from src.accounts.enums import (
    NotificationType,
    UserStatus,
    UserType,
)
from src.accounts.models import Notification
from src.accounts.serializers.notifications import (
    NotificationTaskSerializer,
    NotificationWorkflowSerializer,
)
from src.accounts.tokens import ResetPasswordToken
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.celery_app import periodic_lock
from src.executor import RawSqlExecutor
from src.notifications.enums import (
    NotificationMethod,
)
from src.notifications.messages import MSG_NF_0001
from src.notifications.queries import (
    UsersWithOverdueTaskQuery, UsersWithRemainderTaskQuery,
)
from src.notifications.services.email import (
    EmailService,
)
from src.notifications.services.push import (
    PushNotificationService,
)
from src.notifications.services.websockets import (
    WebSocketService,
)
from src.processes.models.workflows.event import (
    WorkflowEvent,
    WorkflowEventAction,
)
from src.processes.models.workflows.task import (
    Task,
    TaskPerformer,
)
from src.processes.models.workflows.workflow import Workflow
from src.processes.serializers.workflows.events import (
    WorkflowEventSerializer,
)
from src.processes.utils.common import get_duration_format
from src.services.html_converter import convert_text_to_html
from src.services.markdown import MarkdownService

UserModel = get_user_model()


__all__ = [
    'send_comment_notification',
    'send_complete_task_notification',
    'send_completed_workflow_notification',
    'send_delayed_workflow_notification',
    'send_due_date_changed',
    'send_group_created_notification',
    'send_group_deleted_notification',
    'send_group_updated_notification',
    'send_guest_new_task',
    'send_invite_notification',
    'send_mention_notification',
    'send_new_task_notification',
    'send_new_task_websocket',
    'send_not_urgent_notification',
    'send_overdue_task_notification',
    'send_reaction_notification',
    'send_remainder_task_notification',
    'send_removed_task_notification',
    'send_reset_password_notification',
    'send_resumed_workflow_notification',
    'send_tasks_digest_notification',
    'send_unread_notifications',
    'send_urgent_notification',
    'send_user_created_notification',
    'send_user_deactivated_notification',
    'send_user_deleted_notification',
    'send_user_transfer_notification',
    'send_user_updated_notification',
    'send_verification_notification',
    'send_workflow_comment_watched',
    'send_workflow_event',
    'send_workflows_digest_notification',
]


class NotificationTask(TaskCelery):
    autoretry_for = (FirebaseError, )
    retry_backoff = True


def _send_notification(
    method_name: NotificationMethod.LITERALS,
    user_id: int,
    user_email: str,
    account_id: int,
    logo_lg: Optional[str] = None,
    logging: bool = False,
    **kwargs,
):

    services = {
        PushNotificationService,
        EmailService,
        WebSocketService,
    }
    for service_cls in services:
        if method_name in service_cls.ALLOWED_METHODS:
            service = service_cls(
                logging=logging,
                account_id=account_id,
                logo_lg=logo_lg,
            )
            send_method = getattr(service, f'send_{method_name}')
            send_method(
                user_email=user_email,
                user_id=user_id,
                **kwargs,
            )


def _send_new_task_notification(
    logging: bool,
    account_id: int,
    recipients: List[Tuple[int, str, bool]],
    task_id: int,
    task_name: str,
    workflow_name: str,
    template_name: str,
    workflow_starter_name: Optional[str] = None,
    workflow_starter_photo: Optional[str] = None,
    due_date_timestamp: Optional[int] = None,
    task_description: Optional[str] = None,
    logo_lg: Optional[str] = None,
    is_returned: bool = False,
    task_data: Optional[dict] = None,
):
    method_name = (
        NotificationMethod.returned_task
        if is_returned else
        NotificationMethod.new_task
    )
    if not workflow_starter_name:
        workflow_starter_name = 'External User'
        workflow_starter_photo = None

    if task_data is None:
        task = Task.objects.select_related('workflow').get(id=task_id)
        task_data = task.get_data_for_list()

    due_in = None
    overdue = None
    if due_date_timestamp:
        tz = pytz.timezone(settings.TIME_ZONE)
        aware_due_date = datetime.fromtimestamp(due_date_timestamp, tz=tz)
        due_date_duration = aware_due_date - timezone.now()
        formatted_date = get_duration_format(duration=due_date_duration)
        if due_date_duration.total_seconds() > 0:
            due_in = formatted_date
        else:
            overdue = formatted_date
    if task_description:
        html_description = convert_text_to_html(text=task_description)
        text_description = MarkdownService.clear(text=task_description)
    else:
        html_description = None
        text_description = None
    link = f'{settings.FRONTEND_URL}/tasks/{task_id}'

    for (user_id, user_email, is_subscribed) in recipients:
        if is_subscribed:
            _send_notification(
                logging=logging,
                account_id=account_id,
                method_name=method_name,
                user_id=user_id,
                user_email=user_email,
                wf_starter_name=workflow_starter_name,
                wf_starter_photo=workflow_starter_photo,
                logo_lg=logo_lg,
                template_name=template_name,
                workflow_name=workflow_name,
                task_id=task_id,
                task_name=task_name,
                task_data=task_data,
                html_description=html_description,
                text_description=text_description,
                due_in=due_in,
                overdue=overdue,
                link=link,
                sync=True,
            )


def _send_new_task_websocket(
    logging: bool,
    account_id: int,
    recipients: List[Tuple[int, str, bool]],
    task_id: int,
    task_data: Optional[dict] = None,
    **kwargs,
):
    if task_data is None:
        task = Task.objects.select_related('workflow').get(id=task_id)
        task_data = task.get_data_for_list()
    link = f'{settings.FRONTEND_URL}/tasks/{task_id}'
    for (user_id, user_email, _) in recipients:
        _send_notification(
            logging=logging,
            account_id=account_id,
            method_name=NotificationMethod.new_task_websocket,
            user_id=user_id,
            user_email=user_email,
            task_data=task_data,
            link=link,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_new_task_notification(**kwargs):
    _send_new_task_websocket(**kwargs)
    _send_new_task_notification(**kwargs)


@shared_task(base=NotificationTask)
def send_new_task_websocket(**kwargs):
    _send_new_task_websocket(**kwargs)


def _send_removed_task_notification(
    task_id: int,
    recipients: List[Tuple[int, str]],
    account_id: int,
    task_data: Optional[dict] = None,
    **kwargs,
):

    if task_data is None:
        task = Task.objects.select_related('workflow').get(id=task_id)
        task_data = task.get_data_for_list()

    link = f'{settings.FRONTEND_URL}/tasks/{task_id}'
    for (user_id, user_email) in recipients:
        _send_notification(
            method_name=NotificationMethod.removed_task,
            user_id=user_id,
            user_email=user_email,
            account_id=account_id,
            task_data=task_data,
            link=link,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_removed_task_notification(**kwargs):
    _send_removed_task_notification(**kwargs)


def _send_complete_task_notification(
    logging: bool,
    author_id: int,
    account_id: int,
    recipients: List[Tuple[int, str]],
    task_id: int,
    logo_lg: Optional[str] = None,
):
    task = Task.objects.select_related('workflow').get(id=task_id)
    task_json = NotificationTaskSerializer(
        instance=task,
        notification_type=NotificationType.COMPLETE_TASK,
    ).data
    link = f'{settings.FRONTEND_URL}/tasks/{task_id}'
    workflow_json = NotificationWorkflowSerializer(instance=task.workflow).data
    for (user_id, user_email) in recipients:
        notification = Notification.objects.create(
            task=task,
            task_json=task_json,
            workflow_json=workflow_json,
            user_id=user_id,
            author_id=author_id,
            account_id=account_id,
            type=NotificationType.COMPLETE_TASK,
        )
        _send_notification(
            logging=logging,
            logo_lg=logo_lg,
            user_id=user_id,
            user_email=user_email,
            account_id=account_id,
            notification=notification,
            method_name=NotificationMethod.complete_task,
            workflow_name=task.workflow.name,
            task_id=task.id,
            task_name=task.name,
            link=link,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_complete_task_notification(**kwargs):
    _send_complete_task_notification(**kwargs)


def _send_overdue_task_notification():
    query = UsersWithOverdueTaskQuery()
    overdue_task_users = RawSqlExecutor.fetch(
        *query.get_sql(),
        stream=True,
        fetch_size=50,
    )
    notifications = []
    send_data = []
    for elem in overdue_task_users:
        task = Task.objects.select_related('workflow').get(id=elem['task_id'])
        task_json = NotificationTaskSerializer(
            instance=task,
            notification_type=NotificationType.OVERDUE_TASK,
        ).data
        workflow_json = NotificationWorkflowSerializer(
            instance=task.workflow,
        ).data
        notification = Notification(
            task=task,
            task_json=task_json,
            workflow_json=workflow_json,
            user_id=elem['user_id'],
            account_id=elem['account_id'],
            type=NotificationType.OVERDUE_TASK,
        )
        if elem['user_type'] == UserType.GUEST:
            token = GuestJWTAuthService.get_str_token(
                task_id=elem['task_id'],
                user_id=elem['user_id'],
                account_id=elem['account_id'],
            )
            elem['token'] = token
            elem['link'] = (
                f'{settings.FRONTEND_URL}/guest-task/{elem["task_id"]}'
                f'?token={token}&utm_campaign=guestUser'
                f'&utm_term={elem["user_id"]}'
            )
        else:
            elem['token'] = None
            elem['link'] = f'{settings.FRONTEND_URL}/tasks/{elem["task_id"]}'
        notifications.append(notification)
        elem['method_name'] = NotificationMethod.overdue_task
        elem['notification'] = notification
        elem['sync'] = True
        send_data.append(elem)

    Notification.objects.bulk_create(notifications)
    for elem in send_data:
        _send_notification(**elem)


@shared_task(base=NotificationTask)
def send_overdue_task_notification():
    with periodic_lock('send_overdue_task_notification') as acquired:
        if not acquired:
            return
    _send_overdue_task_notification()


def _send_remainder_task_notification():
    query = UsersWithRemainderTaskQuery()
    users = RawSqlExecutor.fetch(
        *query.get_sql(),
        stream=True,
        fetch_size=50,
    )
    for elem in users:
        if elem['user_type'] == UserType.GUEST:
            token = GuestJWTAuthService.get_str_token(
                task_id=elem['task_id'],
                user_id=elem['user_id'],
                account_id=elem['account_id'],
            )
            elem['token'] = token
            elem['link'] = (
                f'{settings.FRONTEND_URL}/guest-task/{elem["task_id"]}'
                f'?token={token}&utm_campaign=guestUser'
                f'&utm_term={elem["user_id"]}'
            )
        else:
            elem['token'] = None
            elem['link'] = f'{settings.FRONTEND_URL}/tasks'
        _send_notification(**elem)


@shared_task(base=NotificationTask)
def send_remainder_task_notification():
    with periodic_lock('send_remainder_task_notification') as acquired:
        if not acquired:
            return
    _send_remainder_task_notification()


def _send_workflows_digest_notification(
    user_id: int,
    user_email: str,
    account_id: int,
    date_from: str,
    date_to: str,
    digest: dict,
    logo_lg: Optional[str] = None,
    logging: bool = False,
):
    """Send workflows digest notification through notification system."""

    link = (
        f'{settings.FRONTEND_URL}/workflows'
        f'?utm_source=email&utm_campaign=digest'
    )
    _send_notification(
        method_name=NotificationMethod.workflows_digest,
        user_id=user_id,
        user_email=user_email,
        account_id=account_id,
        logo_lg=logo_lg,
        logging=logging,
        date_from=date_from,
        date_to=date_to,
        digest=digest,
        link=link,
        sync=True,
    )


@shared_task(base=NotificationTask)
def send_workflows_digest_notification(**kwargs):
    _send_workflows_digest_notification(**kwargs)


def _send_tasks_digest_notification(
    user_id: int,
    user_email: str,
    account_id: int,
    date_from: str,
    date_to: str,
    digest: dict,
    logo_lg: Optional[str] = None,
    logging: bool = False,
):
    """Send tasks digest notification through notification system."""

    link = (
        f'{settings.FRONTEND_URL}/tasks'
        f'?utm_source=email&utm_campaign=tasks_digest'
    )

    _send_notification(
        method_name=NotificationMethod.tasks_digest,
        user_id=user_id,
        user_email=user_email,
        account_id=account_id,
        logo_lg=logo_lg,
        logging=logging,
        date_from=date_from,
        date_to=date_to,
        digest=digest,
        link=link,
        sync=True,
    )


@shared_task(base=NotificationTask)
def send_tasks_digest_notification(**kwargs):
    _send_tasks_digest_notification(**kwargs)


def _send_user_deactivated_notification(
    user_id: int,
    user_email: str,
    account_id: int,
    logo_lg: Optional[str] = None,
    logging: bool = False,
):
    """Send user deactivated notification through notification system."""

    _send_notification(
        method_name=NotificationMethod.user_deactivated,
        user_id=user_id,
        user_email=user_email,
        account_id=account_id,
        logo_lg=logo_lg,
        logging=logging,
        link=settings.FRONTEND_URL,
        sync=True,
    )


@shared_task(base=NotificationTask)
def send_user_deactivated_notification(**kwargs):
    _send_user_deactivated_notification(**kwargs)


def _send_user_transfer_notification(
    user_id: int,
    user_email: str,
    account_id: int,
    invited_by_name: str,
    company_name: str,
    token: str,
    logo_lg: Optional[str] = None,
    logging: bool = False,
):
    """Send user transfer notification through notification system."""

    link = (
        f'{settings.BACKEND_URL}/accounts/users/{user_id}/transfer'
        f'?token={token}&utm_source=invite&utm_campaign=transfer'
    )

    _send_notification(
        method_name=NotificationMethod.user_transfer,
        user_id=user_id,
        user_email=user_email,
        account_id=account_id,
        logo_lg=logo_lg,
        logging=logging,
        invited_by_name=invited_by_name,
        company_name=company_name,
        token=token,
        link=link,
        sync=True,
    )


@shared_task(base=NotificationTask)
def send_user_transfer_notification(**kwargs):
    _send_user_transfer_notification(**kwargs)


def _send_verification_notification(
    user_id: int,
    user_email: str,
    account_id: int,
    user_first_name: str,
    token: str,
    logo_lg: Optional[str] = None,
    logging: bool = False,
):
    """Send verification notification through notification system."""

    link = f'{settings.FRONTEND_URL}/auth/verification?token={token}'
    _send_notification(
        method_name=NotificationMethod.verification,
        user_id=user_id,
        user_email=user_email,
        account_id=account_id,
        logo_lg=logo_lg,
        logging=logging,
        user_first_name=user_first_name,
        token=token,
        link=link,
        sync=True,
    )


@shared_task(base=NotificationTask)
def send_verification_notification(**kwargs):
    _send_verification_notification(**kwargs)


def _send_invite_notification(
    user_id: int,
    user_email: str,
    account_id: int,
    token: str,
    logo_lg: Optional[str] = None,
    logging: bool = False,
):
    """Send invite notification through notification system."""

    link = f'{settings.FRONTEND_URL}/auth/signup/invite/?token={token}'

    _send_notification(
        method_name=NotificationMethod.invite,
        account_id=account_id,
        user_id=user_id,
        user_email=user_email,
        logo_lg=logo_lg,
        logging=logging,
        token=token,
        link=link,
        sync=True,
    )


@shared_task(base=NotificationTask)
def send_invite_notification(**kwargs):
    _send_invite_notification(**kwargs)


def _send_resumed_workflow_notification(
    logging: bool,
    author_id: int,
    account_id: int,
    task_id: int,
    logo_lg: Optional[str] = None,
):
    task = Task.objects.select_related('workflow').get(id=task_id)
    users = (
        TaskPerformer.objects
        .by_task(task.id)
        .exclude_directly_deleted()
        .not_completed()
        .order_by('id')
        .get_user_emails_and_ids_set()
    )
    task_json = NotificationTaskSerializer(
        instance=task,
        notification_type=NotificationType.RESUME_WORKFLOW,
    ).data
    link = f'{settings.FRONTEND_URL}/workflows/{task.workflow_id}'
    workflow_json = NotificationWorkflowSerializer(instance=task.workflow).data
    for (user_id, user_email) in users:
        notification = Notification.objects.create(
            task=task,
            task_json=task_json,
            workflow_json=workflow_json,
            user_id=user_id,
            author_id=author_id,
            account_id=account_id,
            type=NotificationType.RESUME_WORKFLOW,
        )
        _send_notification(
            logging=logging,
            method_name=NotificationMethod.resume_workflow,
            user_id=user_id,
            user_email=user_email,
            account_id=account_id,
            logo_lg=logo_lg,
            notification=notification,
            task_id=task.id,  # TODO Deprecated
            workflow_name=task.workflow.name,
            workflow_id=task.workflow_id,
            author_id=author_id,
            link=link,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_resumed_workflow_notification(**kwargs):
    _send_resumed_workflow_notification(**kwargs)


def _send_delayed_workflow_notification(
    logging: bool,
    author_id: int,
    user_id: int,
    user_email: str,
    account_id: int,
    task_id: int,
    logo_lg: Optional[str] = None,
):
    task = Task.objects.select_related('workflow').get(id=task_id)
    task_json = NotificationTaskSerializer(
        instance=task,
        notification_type=NotificationType.DELAY_WORKFLOW,
    ).data
    link = f'{settings.FRONTEND_URL}/workflows/{task.workflow_id}'
    workflow_json = NotificationWorkflowSerializer(instance=task.workflow).data
    notification = Notification.objects.create(
        task=task,
        task_json=task_json,
        workflow_json=workflow_json,
        user_id=user_id,
        author_id=author_id,
        account_id=account_id,
        type=NotificationType.DELAY_WORKFLOW,
    )
    _send_notification(
        logging=logging,
        user_id=user_id,
        user_email=user_email,
        account_id=account_id,
        logo_lg=logo_lg,
        notification=notification,
        method_name=NotificationMethod.delay_workflow,
        task_id=task.id,
        workflow_id=task.workflow_id,
        workflow_name=task.workflow.name,
        author_id=author_id,
        link=link,
        sync=True,
    )


@shared_task(base=NotificationTask)
def send_delayed_workflow_notification(**kwargs):
    _send_delayed_workflow_notification(**kwargs)


def _send_completed_workflow_notification(
    logging: bool,
    workflow_id: int,
    logo_lg: Optional[str] = None,
):
    workflow = Workflow.objects.get(id=workflow_id)
    workflow_json = NotificationWorkflowSerializer(instance=workflow).data
    users = (
        TaskPerformer.objects
        .acd_task_status()
        .users()
        .by_workflow(workflow_id)
        .exclude_directly_deleted()
        .order_by('id')
        .get_user_ids_emails_subscriber_set()
    )
    link = f'{settings.FRONTEND_URL}/workflows/{workflow_id}'

    for (user_id, user_email, is_subscriber) in users:
        if is_subscriber:
            notification = Notification.objects.create(
                workflow_json=workflow_json,
                user_id=user_id,
                account_id=workflow.account_id,
                type=NotificationType.COMPLETE_WORKFLOW,
            )
            _send_notification(
                logging=logging,
                logo_lg=logo_lg,
                user_id=user_id,
                user_email=user_email,
                account_id=workflow.account_id,
                notification=notification,
                method_name=NotificationMethod.complete_workflow,
                workflow_id=workflow.id,
                workflow_name=workflow.name,
                link=link,
                sync=True,
            )


@shared_task(base=NotificationTask)
def send_completed_workflow_notification(**kwargs):
    _send_completed_workflow_notification(**kwargs)


def _send_guest_new_task(
    logging: bool,
    user_id: int,
    user_email: str,
    account_id: int,
    token: str,
    sender_name: str,
    task_id: int,
    task_name: str,
    task_description: str,
    task_due_date: Optional[datetime],
    logo_lg: Optional[str],
):
    link = (
        f'{settings.FRONTEND_URL}/guest-task/{task_id}'
        f'?token={token}&utm_campaign=guestUser&utm_term={user_id}'
    )
    _send_notification(
        logging=logging,
        method_name=NotificationMethod.guest_new_task,
        user_id=user_id,
        user_email=user_email,
        account_id=account_id,
        token=token,
        sender_name=sender_name,
        task_id=task_id,
        task_name=task_name,
        task_description=task_description,
        task_due_date=task_due_date,
        link=link,
        logo_lg=logo_lg,
    )


@shared_task(base=NotificationTask)
def send_guest_new_task(**kwargs):
    _send_guest_new_task(**kwargs)


def _send_unread_notifications():

    timeout = timedelta(seconds=settings.UNREAD_NOTIFICATIONS_TIMEOUT)
    not_read_timeout_date = (timezone.now() - timeout)
    users = (
        UserModel.objects
        .select_related('account')
        .active()
        .is_comments_mentions_subscriber()
        .with_timeout_to_read_notifications(not_read_timeout_date)
    )
    link = (
        f'{settings.FRONTEND_URL}'
        '?utm_source=notifications&utm_campaign=unread_notifications'
    )
    user_ids = []
    for user in users:
        _send_notification(
            logging=user.account.log_api_requests,
            method_name=NotificationMethod.unread_notifications,
            user_id=user.id,
            account_id=user.account_id,
            user_first_name=user.first_name,
            user_email=user.email,
            logo_lg=user.account.logo_lg,
            link=link,
        )
        user_ids.append(user.id)
    Notification.objects.timeout_to_read(
        user_ids=user_ids,
        not_read_timeout_date=not_read_timeout_date,
    ).update(is_notified_about_not_read=True)


@shared_task(base=NotificationTask)
def send_unread_notifications():
    _send_unread_notifications()


def _send_due_date_changed(
    logging: bool,
    author_id: int,
    task_id: int,
    account_id: int,
    logo_lg: Optional[str],
):
    task = Task.objects.select_related('workflow').get(id=task_id)
    link = f'{settings.FRONTEND_URL}/tasks/{task_id}'
    users = (
        TaskPerformer.objects
        .by_task(task_id)
        .exclude_directly_deleted()
        .not_completed()
        .get_user_emails_and_ids_set()
    )
    users = {user for user in users if user[0] != author_id}
    task_json = NotificationTaskSerializer(
        instance=task,
        notification_type=NotificationType.DUE_DATE_CHANGED,
    ).data
    workflow_json = NotificationWorkflowSerializer(instance=task.workflow).data
    for (user_id, user_email) in users:
        notification = Notification.objects.create(
            task=task,
            task_json=task_json,
            workflow_json=workflow_json,
            user_id=user_id,
            author_id=author_id,
            account_id=account_id,
            type=NotificationType.DUE_DATE_CHANGED,
        )
        _send_notification(
            logging=logging,
            method_name=NotificationMethod.due_date_changed,
            user_id=user_id,
            user_email=user_email,
            account_id=account_id,
            logo_lg=logo_lg,
            notification=notification,
            workflow_name=task.workflow.name,
            task_name=task.name,
            task_id=task_id,
            user_type=UserType.USER,
            link=link,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_due_date_changed(**kwargs):
    _send_due_date_changed(**kwargs)


def _send_urgent_notification(
    logging: bool,
    author_id: int,
    task_ids: List[int],
    account_id: int,
    logo_lg: Optional[str],
    notification_type: NotificationType.URGENT_TYPES,
    method_name: NotificationMethod.LITERALS,
):
    for task_id in task_ids:
        task = Task.objects.select_related('workflow').get(id=task_id)
        link = f'{settings.FRONTEND_URL}/workflows/{task.id}'
        users = (
            TaskPerformer.objects
            .by_task(task_id)
            .exclude_directly_deleted()
            .not_completed()
            .order_by('id')
            .get_user_emails_and_ids_set()
        )
        users = {user for user in users if user[0] != author_id}
        task_json = NotificationTaskSerializer(
            instance=task,
            notification_type=notification_type,
        ).data
        workflow_json = NotificationWorkflowSerializer(
            instance=task.workflow,
        ).data
        for (user_id, user_email) in users:
            notification = Notification.objects.create(
                task=task,
                task_json=task_json,
                workflow_json=workflow_json,
                user_id=user_id,
                author_id=author_id,
                account_id=account_id,
                type=notification_type,
            )
            _send_notification(
                logging=logging,
                notification=notification,
                method_name=method_name,
                account_id=account_id,
                logo_lg=logo_lg,
                user_id=user_id,
                user_email=user_email,
                link=link,
                sync=True,
            )


@shared_task(base=NotificationTask)
def send_urgent_notification(**kwargs):
    _send_urgent_notification(
        notification_type=NotificationType.URGENT,
        method_name=NotificationMethod.urgent,
        **kwargs,
    )


@shared_task(base=NotificationTask)
def send_not_urgent_notification(**kwargs):
    _send_urgent_notification(
        notification_type=NotificationType.NOT_URGENT,
        method_name=NotificationMethod.not_urgent,
        **kwargs,
    )


def _send_comment_notification(
    logging: bool,
    account_id: int,
    logo_lg: Optional[str],
    author_id: int,
    event_id: int,
    users_ids: Tuple[int],
    text: Optional[str] = None,
):
    event = WorkflowEvent.objects.select_related(
        'workflow', 'task',
    ).get(id=event_id)
    users = (
        UserModel.objects
        .on_account(account_id)
        .filter(id__in=users_ids)
        .order_by('id')
        .values_list('id', 'email')
    )
    workflow_json = NotificationWorkflowSerializer(
        instance=event.workflow,
    ).data
    if event.task:
        task_json = NotificationTaskSerializer(
            instance=event.task,
            notification_type=NotificationType.COMMENT,
        ).data
    else:
        task_json = {
            'id': event.task_json['id'],
            'name': event.task_json['name'],
        }
    link = f'{settings.FRONTEND_URL}/tasks/{task_json["id"]}'
    for (user_id, user_email) in users:
        notification = Notification.objects.create(
            task_id=task_json['id'],
            task_json=task_json,
            workflow_json=workflow_json,
            user_id=user_id,
            author_id=author_id,
            account_id=account_id,
            type=NotificationType.COMMENT,
            text=text,
        )
        _send_notification(
            logging=logging,
            user_id=user_id,
            user_email=user_email,
            account_id=account_id,
            logo_lg=logo_lg,
            notification=notification,
            method_name=NotificationMethod.comment,
            task_id=task_json['id'],
            link=link,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_comment_notification(**kwargs):
    _send_comment_notification(**kwargs)


def _send_mention_notification(
    logging: bool,
    account_id: int,
    logo_lg: Optional[str],
    author_id: int,
    event_id: int,
    users_ids: Tuple[int],
    text: Optional[str] = None,
):
    event = WorkflowEvent.objects.select_related(
        'workflow', 'task',
    ).get(id=event_id)
    users = (
        UserModel.objects
        .on_account(account_id)
        .filter(id__in=users_ids)
        .order_by('id')
        .values_list('id', 'email', 'first_name')
    )
    workflow_json = NotificationWorkflowSerializer(
        instance=event.workflow,
    ).data
    if event.task:
        task_json = NotificationTaskSerializer(
            instance=event.task,
            notification_type=NotificationType.MENTION,
        ).data
    else:
        task_json = {
            'id': event.task_json['id'],
            'name': event.task_json['name'],
        }
    link = f'{settings.FRONTEND_URL}/tasks/{task_json["id"]}'
    for (user_id, user_email, user_first_name) in users:
        notification = Notification.objects.create(
            task_id=task_json['id'],
            task_json=task_json,
            workflow_json=workflow_json,
            user_id=user_id,
            author_id=author_id,
            account_id=account_id,
            type=NotificationType.MENTION,
            text=text,
        )
        _send_notification(
            logging=logging,
            user_id=user_id,
            user_email=user_email,
            user_first_name=user_first_name,
            account_id=account_id,
            logo_lg=logo_lg,
            notification=notification,
            method_name=NotificationMethod.mention,
            task_id=task_json['id'],
            link=link,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_mention_notification(**kwargs):
    _send_mention_notification(**kwargs)


def _send_workflow_event(
    logging: bool,
    account_id: int,
    logo_lg: Optional[str],
    data: dict,
):

    """ Send ws when workflow event created/updated """

    users = (
        Workflow.members.through.objects.filter(
            workflow_id=data['workflow_id'],
            user__status=UserStatus.ACTIVE,
        )
        .order_by('user_id')
        .values_list('user_id', 'user__email')
    )
    for (user_id, user_email) in users:
        _send_notification(
            logging=logging,
            method_name=NotificationMethod.workflow_event,
            data=data,
            user_id=user_id,
            user_email=user_email,
            account_id=account_id,
            logo_lg=logo_lg,
            sync=True,
        )

    if data.get('task'):
        guests = (
            TaskPerformer.objects
            .by_task(data['task']['id'])
            .guests()
            .exclude_directly_deleted()
            .values_list('user_id', 'user__email')
        )
        for (guest_id, guest_email) in guests:
            _send_notification(
                logging=logging,
                method_name=NotificationMethod.workflow_event,
                data=data,
                user_id=guest_id,
                user_email=guest_email,
                account_id=account_id,
                logo_lg=logo_lg,
                sync=True,
            )


@shared_task(base=NotificationTask)
def send_workflow_event(**kwargs):
    _send_workflow_event(**kwargs)


def _send_workflow_comment_watched():

    new_actions_ids = WorkflowEventAction.objects.watched().only_ids()
    if new_actions_ids:
        with transaction.atomic():
            modified_events = WorkflowEvent.objects.update_watched_from(
                new_actions_ids,
            )
            WorkflowEventAction.objects.filter(id__in=new_actions_ids).delete()
        modified_events_ids = (el.id for el in modified_events)
        events = (
            WorkflowEvent.objects
            .prefetch_related('attachments')
            .select_related('account')
            .filter(id__in=modified_events_ids)
            .type_comment()
        )
        for event in events:
            data = WorkflowEventSerializer(instance=event).data
            _send_workflow_event(
                data=data,
                account_id=event.account_id,
                logo_lg=event.account.logo_lg,
                logging=event.account.log_api_requests,
            )


@shared_task(base=NotificationTask)
def send_workflow_comment_watched():
    lock_expire = 60  # 1 min
    with periodic_lock('comment_watched', lock_expire) as acquired:
        if not acquired:
            return
    _send_workflow_comment_watched()


def _send_reaction_notification(
    logging: bool,
    author_id: int,
    account_id: int,
    user_id: int,
    user_email: str,
    logo_lg: Optional[str],
    author_name: str,
    reaction: str,
    event_id: int,
):
    event = WorkflowEvent.objects.select_related(
        'workflow', 'task',
    ).get(id=event_id)
    workflow_json = NotificationWorkflowSerializer(
        instance=event.workflow,
    ).data
    if event.task:
        task_json = NotificationTaskSerializer(
            instance=event.task,
            notification_type=NotificationType.REACTION,
        ).data
    else:
        task_json = {
            'id': event.task_json['id'],
            'name': event.task_json['name'],
        }
    link = f'{settings.FRONTEND_URL}/tasks/{task_json["id"]}'
    text = MSG_NF_0001(reaction)
    notification = Notification.objects.create(
        task_id=task_json['id'],
        task_json=task_json,
        workflow_json=workflow_json,
        user_id=user_id,
        author_id=author_id,
        account_id=account_id,
        type=NotificationType.REACTION,
        text=text,
    )
    _send_notification(
        logging=logging,
        user_id=user_id,
        user_email=user_email,
        logo_lg=logo_lg,
        account_id=account_id,
        notification=notification,
        method_name=NotificationMethod.reaction,
        author_name=author_name,
        task_id=task_json['id'],
        workflow_name=workflow_json['name'],
        text=text,
        link=link,
        sync=True,
    )


@shared_task(base=NotificationTask)
def send_reaction_notification(**kwargs):
    _send_reaction_notification(**kwargs)


def _send_reset_password_notification(
    logging: bool,
    user_id: int,
    user_email: str,
    account_id: int,
    logo_lg: Optional[str] = None,
):

    token = ResetPasswordToken.for_user_id(user_id).__str__()
    link = f'{settings.FRONTEND_URL}/auth/reset-password/?token={token}'
    _send_notification(
        logging=logging,
        method_name=NotificationMethod.reset_password,
        user_id=user_id,
        user_email=user_email,
        account_id=account_id,
        logo_lg=logo_lg,
        link=link,
        token=token,
        sync=True,
    )


@shared_task(base=NotificationTask)
def send_reset_password_notification(**kwargs):
    _send_reset_password_notification(**kwargs)


def _send_group_created_notification(
    logging: bool,
    account_id: int,
    group_data: dict,
    **kwargs,
):
    users = UserModel.objects.filter(
        account_id=account_id,
        status=UserStatus.ACTIVE,
    ).values_list('id', 'email')

    for (user_id, user_email) in users:
        _send_notification(
            method_name=NotificationMethod.group_created,
            account_id=account_id,
            user_id=user_id,
            user_email=user_email,
            logging=logging,
            group_data=group_data,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_group_created_notification(**kwargs):
    _send_group_created_notification(**kwargs)


def _send_group_updated_notification(
    logging: bool,
    account_id: int,
    group_data: dict,
    **kwargs,
):
    users = UserModel.objects.filter(
        account_id=account_id,
        status=UserStatus.ACTIVE,
    ).values_list('id', 'email')

    for (user_id, user_email) in users:
        _send_notification(
            method_name=NotificationMethod.group_updated,
            account_id=account_id,
            user_id=user_id,
            user_email=user_email,
            logging=logging,
            group_data=group_data,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_group_updated_notification(**kwargs):
    _send_group_updated_notification(**kwargs)


def _send_group_deleted_notification(
    logging: bool,
    account_id: int,
    group_data: dict,
    **kwargs,
):
    users = UserModel.objects.filter(
        account_id=account_id,
        status=UserStatus.ACTIVE,
    ).values_list('id', 'email')

    for (user_id, user_email) in users:
        _send_notification(
            method_name=NotificationMethod.group_deleted,
            account_id=account_id,
            user_id=user_id,
            user_email=user_email,
            logging=logging,
            group_data=group_data,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_group_deleted_notification(**kwargs):
    _send_group_deleted_notification(**kwargs)


def _send_user_created_notification(
    logging: bool,
    account_id: int,
    user_data: dict,
    **kwargs,
):
    users = UserModel.objects.filter(
        account_id=account_id,
        status=UserStatus.ACTIVE,
    ).values_list('id', 'email')

    for (user_id, user_email) in users:
        _send_notification(
            method_name=NotificationMethod.user_created,
            account_id=account_id,
            user_id=user_id,
            user_email=user_email,
            logging=logging,
            user_data=user_data,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_user_created_notification(**kwargs):
    _send_user_created_notification(**kwargs)


def _send_user_updated_notification(
    logging: bool,
    account_id: int,
    user_data: dict,
    **kwargs,
):
    users = UserModel.objects.filter(
        account_id=account_id,
        status=UserStatus.ACTIVE,
    ).values_list('id', 'email')

    for (user_id, user_email) in users:
        _send_notification(
            method_name=NotificationMethod.user_updated,
            account_id=account_id,
            user_id=user_id,
            user_email=user_email,
            logging=logging,
            user_data=user_data,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_user_updated_notification(**kwargs):
    _send_user_updated_notification(**kwargs)


def _send_user_deleted_notification(
    logging: bool,
    account_id: int,
    user_data: dict,
    **kwargs,
):
    users = UserModel.objects.filter(
        account_id=account_id,
        status=UserStatus.ACTIVE,
    ).values_list('id', 'email')

    for (user_id, user_email) in users:
        _send_notification(
            method_name=NotificationMethod.user_deleted,
            account_id=account_id,
            user_id=user_id,
            user_email=user_email,
            logging=logging,
            user_data=user_data,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_user_deleted_notification(**kwargs):
    _send_user_deleted_notification(**kwargs)
