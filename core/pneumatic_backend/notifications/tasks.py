import pytz
from typing import Optional, Tuple, List
from datetime import datetime
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
            service = service_cls(logging=logging)
            send_method = getattr(service, f'send_{method_name}')
            send_method(
                user_id=user_id,
                **kwargs,
            )


def _send_new_task_notification(
    logging: bool,
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
    for recipient in recipients:
        _send_notification(
            logging=logging,
            method_name=method_name,
            user_id=recipient[0],
            user_email=recipient[1],
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
            notification=notification,
            method_name=NotificationMethod.complete_task,
            user_id=user_id,
            user_email=user_email,
            logo_lg=logo_lg,
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
):
    user_ids = (
        TaskPerformer.objects
        .by_task(task_id).exclude_directly_deleted(
        ).not_completed().users().order_by(
            'id'
        ).values_list('user_id', flat=True)
    )
    for user_id in user_ids:
        notification = Notification.objects.create(
            task_id=task_id,
            user_id=user_id,
            author_id=author_id,
            account_id=account_id,
            type=NotificationType.RESUME_WORKFLOW,
        )
        _send_notification(
            logging=logging,
            notification=notification,
            method_name=NotificationMethod.resume_workflow,
            user_id=user_id,
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
    account_id: int,
    workflow_name: str,
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
        notification=notification,
        method_name=NotificationMethod.delay_workflow,
        user_id=user_id,
        task_id=task_id,
        workflow_name=workflow_name,
        author_id=author_id,
        sync=True
    )


@shared_task(base=NotificationTask)
def send_delayed_workflow_notification(**kwargs):
    _send_delayed_workflow_notification(**kwargs)


def _send_guest_new_task(
    user_id: int,
    user_email: str,
    token: str,
    sender_name: str,
    task_id: int,
    task_name: str,
    task_description: str,
    task_due_date: Optional[datetime],
    logo_lg: Optional[str],
):
    _send_notification(
        method_name=NotificationMethod.guest_new_task,
        token=token,
        sender_name=sender_name,
        user_id=user_id,
        user_email=user_email,
        task_id=task_id,
        task_name=task_name,
        task_description=task_description,
        task_due_date=task_due_date,
        logo_lg=logo_lg,
    )


@shared_task(base=NotificationTask)
def send_guest_new_task(user_id: int, **kwargs):
    _send_guest_new_task(user_id, **kwargs)


def _send_unread_notifications():

    not_read_timeout_date = (
        timezone.now() - settings.NOTIFICATIONS_NOT_READ_TIMEOUT
    )
    users = UserModel.objects.select_related(
        'account'
    ).filter(
        account__payment_card_provided=True
    ).active().is_comments_mentions_subscriber(
    ).with_timeout_to_read_notifications(not_read_timeout_date)

    user_ids = []
    for user in users:
        _send_notification(
            method_name=NotificationMethod.unread_notifications,
            user_id=user.id,
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
):
    user_ids = (
        TaskPerformer.objects
        .by_task(task_id)
        .users()
        .exclude(
            user_id=author_id,
            # directly_status=DirectlyStatus.DELETED
        ).exclude_directly_deleted().not_completed()
        .values_list('user_id', flat=True)
    )
    for user_id in user_ids:
        notification = Notification.objects.create(
            task_id=task_id,
            user_id=user_id,
            author_id=author_id,
            account_id=account_id,
            type=NotificationType.DUE_DATE_CHANGED,
        )
        _send_notification(
            logging=logging,
            notification=notification,
            method_name=NotificationMethod.due_date_changed,
            user_id=user_id,
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
    author_id: int,
    task_id: int,
    account_id: int,
    notification_type: NotificationType.URGENT_TYPES,
    method_name: NotificationMethod
):
    users_ids = TaskPerformer.objects.exclude_directly_deleted().by_task(
        task_id
    ).not_completed().users().exclude(
        user_id=author_id
    ).order_by('id').values_list('user_id', flat=True)

    for user_id in users_ids:
        notification = Notification.objects.create(
            task_id=task_id,
            user_id=user_id,
            author_id=author_id,
            account_id=account_id,
            type=notification_type,
        )
        _send_notification(
            notification=notification,
            method_name=method_name,
            user_id=user_id,
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
    author_id: int,
    task_id: int,
    account_id: int,
    users_ids: Tuple[int],
    text: Optional[str] = None,
):
    for user_id in users_ids:
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
            notification=notification,
            method_name=NotificationMethod.comment,
            user_id=user_id,
            task_id=task_id,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_comment_notification(**kwargs):
    _send_comment_notification(**kwargs)


def _send_mention_notification(
    logging: bool,
    author_id: int,
    task_id: int,
    account_id: int,
    users_ids: Tuple[int],
    text: Optional[str] = None,
):
    for user_id in users_ids:
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
            notification=notification,
            method_name=NotificationMethod.mention,
            user_id=user_id,
            task_id=task_id,
            sync=True,
        )


@shared_task(base=NotificationTask)
def send_mention_notification(**kwargs):
    _send_mention_notification(**kwargs)


def _send_workflow_event(data: dict):

    """ Send ws when workflow event created/updated """

    qst = Workflow.members.through.objects.filter(
        workflow_id=data['workflow_id'],
        user__status=UserStatus.ACTIVE
    ).order_by('user_id').values_list('user_id', flat=True)

    for user_id in qst:
        _send_notification(
            method_name=NotificationMethod.workflow_event,
            data=data,
            user_id=user_id,
            sync=True,
        )

    if data.get('task'):
        for guest_id in TaskPerformer.objects.by_task(
            data['task']['id']
        ).guests().exclude_directly_deleted().user_ids():
            _send_notification(
                method_name=NotificationMethod.workflow_event,
                data=data,
                user_id=guest_id,
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
        events = WorkflowEvent.objects.prefetch_related('attachments').filter(
            id__in=modified_events_ids
        ).type_comment()
        for event in events:
            data = WorkflowEventSerializer(instance=event).data
            _send_workflow_event(data)


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
        notification=notification,
        method_name=NotificationMethod.reaction,
        user_id=user_id,
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
    user_id: int,
    user_email: str,
    logo_lg: Optional[str] = None,
):

    _send_notification(
        method_name=NotificationMethod.reset_password,
        user_id=user_id,
        user_email=user_email,
        logo_lg=logo_lg,
        sync=True,
    )


@shared_task(base=NotificationTask)
def send_reset_password_notification(**kwargs):
    _send_reset_password_notification(**kwargs)
