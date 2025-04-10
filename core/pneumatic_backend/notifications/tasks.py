import pytz
from typing import Optional, Tuple, List
from datetime import datetime, timedelta
from celery import shared_task
from celery.task import Task
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from firebase_admin.exceptions import FirebaseError
from pneumatic_backend.accounts.enums import (
    NotificationType,
    UserType,
    UserStatus,
)
from pneumatic_backend.accounts.models import Notification
from pneumatic_backend.notifications.enums import (
    NotificationMethod,
)
from pneumatic_backend.notifications.services.push import (
    PushNotificationService
)
from pneumatic_backend.notifications.services.email import (
    EmailService
)
from pneumatic_backend.notifications.queries import (
    UsersWithOverdueTaskQuery
)
from pneumatic_backend.notifications.services.websockets import (
    WebSocketService
)
from pneumatic_backend.processes.models import (
    TaskPerformer,
    Workflow,
    WorkflowEvent,
    WorkflowEventAction,
)
from pneumatic_backend.processes.api_v2.serializers.workflow.events import (
    WorkflowEventSerializer,
)
from pneumatic_backend.executor import RawSqlExecutor
from pneumatic_backend.celery import periodic_lock
from pneumatic_backend.authentication.services import (
    GuestJWTAuthService
)
from pneumatic_backend.notifications.messages import MSG_NF_0001
from pneumatic_backend.processes.utils.common import get_duration_format
from pneumatic_backend.services.html_converter import convert_text_to_html
from pneumatic_backend.services.markdown import MarkdownService


UserModel = get_user_model()


__all__ = [
    'send_new_task_notification',
    'send_complete_task_notification',
    'send_mention_notification',
    'send_comment_notification',
    'send_overdue_task_notification',
    'send_delayed_workflow_notification',
    'send_resumed_workflow_notification',
    'send_guest_new_task',
    'send_unread_notifications',
    'send_due_date_changed',
    'send_urgent_notification',
    'send_not_urgent_notification',
    'send_workflow_event',
    'send_workflow_comment_watched',
    'send_reaction_notification',
    'send_reset_password_notification',
]


class NotificationTask(Task):
    autoretry_for = (FirebaseError, )
    retry_backoff = True


def _send_notification(
    method_name: NotificationMethod,
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
    recipients: List[Tuple[int, str]],
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
):

    method_name = (
        NotificationMethod.returned_task
        if is_returned else
        NotificationMethod.new_task
    )
    if not workflow_starter_name:
        workflow_starter_name = 'External User'
        workflow_starter_photo = None

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
    for (user_id, user_email) in recipients:
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
            html_description=html_description,
            text_description=text_description,
            due_in=due_in,
            overdue=overdue,
            sync=True
        )


@shared_task(base=NotificationTask)
def send_new_task_notification(**kwargs):
    _send_new_task_notification(**kwargs)


def _send_complete_task_notification(
    logging: bool,
    author_id: int,
    account_id: int,
    recipients: List[Tuple[int, str]],
    task_id: int,
    task_name: str,
    workflow_name: str,
    logo_lg: Optional[str] = None,
):

    for (user_id, user_email) in recipients:
        notification = Notification.objects.create(
            task_id=task_id,
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
            workflow_name=workflow_name,
            task_id=task_id,
            task_name=task_name,
            sync=True
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
        db='replica',
    )
    notifications = []
    send_data = []
    for elem in overdue_task_users:
        notification = Notification(
            task_id=elem['task_id'],
            user_id=elem['user_id'],
            account_id=elem['account_id'],
            type=NotificationType.OVERDUE_TASK,
        )
        if elem['user_type'] == UserType.GUEST:
            elem['token'] = GuestJWTAuthService.get_str_token(
                task_id=elem['task_id'],
                user_id=elem['user_id'],
                account_id=elem['account_id'],
            )
        else:
            elem['token'] = None
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


def _send_resumed_workflow_notification(
    logging: bool,
    task_id: int,
    author_id: int,
    account_id: int,
    workflow_name: str,
    logo_lg: Optional[str] = None,
):
    users = (
        TaskPerformer.objects
        .by_task(task_id)
        .exclude_directly_deleted()
        .not_completed()
        .order_by('id')
        .get_user_emails_and_ids_set()
    )
    for (user_id, user_email) in users:
        notification = Notification.objects.create(
            task_id=task_id,
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
            task_id=task_id,
            workflow_name=workflow_name,
            author_id=author_id,
            sync=True
        )


@shared_task(base=NotificationTask)
def send_resumed_workflow_notification(
    **kwargs
):
    _send_resumed_workflow_notification(**kwargs)


def _send_delayed_workflow_notification(
    logging: bool,
    task_id: int,
    author_id: int,
    user_id: int,
    user_email: str,
    account_id: int,
    workflow_name: str,
    logo_lg: Optional[str] = None,
):
    notification = Notification.objects.create(
        task_id=task_id,
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
        task_id=task_id,
        workflow_name=workflow_name,
        author_id=author_id,
        sync=True
    )


@shared_task(base=NotificationTask)
def send_delayed_workflow_notification(**kwargs):
    _send_delayed_workflow_notification(**kwargs)


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
        )
        user_ids.append(user.id)
    Notification.objects.timeout_to_read(
        user_ids=user_ids,
        not_read_timeout_date=not_read_timeout_date
    ).update(is_notified_about_not_read=True)


@shared_task(base=NotificationTask)
def send_unread_notifications():
    _send_unread_notifications()


def _send_due_date_changed(
    logging: bool,
    author_id: int,
    task_id: int,
    task_name: str,
    workflow_name: str,
    account_id: int,
    logo_lg: Optional[str]
):
    users = (
        TaskPerformer.objects
        .by_task(task_id)
        .exclude_directly_deleted()
        .not_completed()
        .get_user_emails_and_ids_set()
    )
    users = {user for user in users if user[0] != author_id}
    for (user_id, user_email) in users:
        notification = Notification.objects.create(
            task_id=task_id,
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
            workflow_name=workflow_name,
            task_name=task_name,
            task_id=task_id,
            user_type=UserType.USER,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_due_date_changed(**kwargs):
    _send_due_date_changed(**kwargs)


def _send_urgent_notification(
    logging: bool,
    author_id: int,
    task_id: int,
    account_id: int,
    logo_lg: Optional[str],
    notification_type: NotificationType.URGENT_TYPES,
    method_name: NotificationMethod,
):
    users = (
        TaskPerformer.objects
        .by_task(task_id)
        .exclude_directly_deleted()
        .not_completed()
        .order_by('id')
        .get_user_emails_and_ids_set()
    )
    users = {user for user in users if user[0] != author_id}
    for (user_id, user_email) in users:
        notification = Notification.objects.create(
            task_id=task_id,
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
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_urgent_notification(**kwargs):
    _send_urgent_notification(
        notification_type=NotificationType.URGENT,
        method_name=NotificationMethod.urgent,
        **kwargs
    )


@shared_task(base=NotificationTask)
def send_not_urgent_notification(**kwargs):
    _send_urgent_notification(
        notification_type=NotificationType.NOT_URGENT,
        method_name=NotificationMethod.not_urgent,
        **kwargs
    )


def _send_comment_notification(
    logging: bool,
    account_id: int,
    logo_lg: Optional[str],
    author_id: int,
    task_id: int,
    users_ids: Tuple[int],
    text: Optional[str] = None,
):
    users = (
        UserModel.objects
        .on_account(account_id)
        .filter(id__in=users_ids)
        .order_by('id')
        .values_list('id', 'email')
    )
    for (user_id, user_email) in users:
        notification = Notification.objects.create(
            task_id=task_id,
            user_id=user_id,
            author_id=author_id,
            account_id=account_id,
            type=NotificationType.COMMENT,
            text=text
        )
        _send_notification(
            logging=logging,
            user_id=user_id,
            user_email=user_email,
            account_id=account_id,
            logo_lg=logo_lg,
            notification=notification,
            method_name=NotificationMethod.comment,
            task_id=task_id,
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
    task_id: int,
    users_ids: Tuple[int],
    text: Optional[str] = None,
):
    users = (
        UserModel.objects
        .on_account(account_id)
        .filter(id__in=users_ids)
        .order_by('id')
        .values_list('id', 'email', 'first_name')
    )
    for (user_id, user_email, user_first_name) in users:
        notification = Notification.objects.create(
            task_id=task_id,
            user_id=user_id,
            author_id=author_id,
            account_id=account_id,
            type=NotificationType.MENTION,
            text=text
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
            task_id=task_id,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_mention_notification(**kwargs):
    _send_mention_notification(**kwargs)


def _send_workflow_event(
    logging: bool,
    account_id: int,
    logo_lg: Optional[str],
    data: dict
):

    """ Send ws when workflow event created/updated """

    users = (
        Workflow.members.through.objects.filter(
            workflow_id=data['workflow_id'],
            user__status=UserStatus.ACTIVE
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
                new_actions_ids
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
                logging=event.account.log_api_requests
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
    task_id: int,
    account_id: int,
    user_id: int,
    user_email: str,
    logo_lg: Optional[str],
    author_name: str,
    reaction: str,
    workflow_name: str,
):
    text = MSG_NF_0001(reaction)
    notification = Notification.objects.create(
        task_id=task_id,
        user_id=user_id,
        author_id=author_id,
        account_id=account_id,
        type=NotificationType.REACTION,
        text=text
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
        task_id=task_id,
        workflow_name=workflow_name,
        text=text,
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

    _send_notification(
        logging=logging,
        method_name=NotificationMethod.reset_password,
        user_id=user_id,
        user_email=user_email,
        account_id=account_id,
        logo_lg=logo_lg,
        sync=True,
    )


@shared_task(base=NotificationTask)
def send_reset_password_notification(**kwargs):
    _send_reset_password_notification(**kwargs)
