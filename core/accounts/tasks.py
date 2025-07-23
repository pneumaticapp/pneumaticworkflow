from celery import shared_task
from django.db import transaction
from pneumatic_backend.accounts.models import (
    SystemMessage,
    Notification,
)
from pneumatic_backend.accounts.queries import CreateSystemNotificationsQuery
from pneumatic_backend.executor import RawSqlExecutor
from pneumatic_backend.notifications.tasks import _send_notification
from pneumatic_backend.notifications.enums import NotificationMethod


@shared_task
def send_system_notification():
    for system_message in SystemMessage.objects.new():
        query = CreateSystemNotificationsQuery(system_message)
        with transaction.atomic():
            RawSqlExecutor.execute(*query.get_sql())
            system_message.is_delivery_completed = True
            system_message.save()
        notifications = Notification.objects.filter(
            system_message=system_message
        ).select_related('user', 'account').exclude_read()
        for notification in notifications:
            _send_notification(
                logging=notification.account.log_api_requests,
                logo_lg=notification.account.logo_lg,
                account_id=notification.account_id,
                user_id=notification.user_id,
                user_email=notification.user.email,
                sync=True,
                notification=notification,
                method_name=NotificationMethod.system,
            )
