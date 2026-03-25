from celery import shared_task
from django.db import transaction

from src.accounts.models import (
    Notification,
    SystemMessage,
)
from src.accounts.queries import CreateSystemNotificationsQuery
from src.executor import RawSqlExecutor
from src.notifications.enums import NotificationMethod
from pytz import timezone as pytz_tz
from django.contrib.auth import get_user_model
from django.utils import timezone
from src.accounts.enums import AbsenceStatus
from src.accounts.services.vacation import VacationDelegationService
from src.notifications.tasks import _send_notification


@shared_task
def send_system_notification():
    for system_message in SystemMessage.objects.new():
        query = CreateSystemNotificationsQuery(system_message)
        with transaction.atomic():
            RawSqlExecutor.execute(*query.get_sql())
            system_message.is_delivery_completed = True
            system_message.save()
        notifications = Notification.objects.filter(
            system_message=system_message,
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


@shared_task(ignore_result=True)
def process_vacation_schedules():
    """Auto-start and auto-stop vacation delegations.

    Runs every 15 minutes via Celery beat.
    Checks user timezones to determine if vacation should
    start or end based on local date.
    """
    user_model = get_user_model()
    now = timezone.now()

    for user in user_model.objects.filter(
        absence_status=AbsenceStatus.ACTIVE,
        vacation_start_date__isnull=False,
        vacation_substitute_group__isnull=False,
    ):
        user_now = now.astimezone(pytz_tz(user.timezone))
        if user_now.date() >= user.vacation_start_date:
            sub_ids = list(
                user.vacation_substitute_group.users
                .values_list('id', flat=True),
            )
            if sub_ids:
                VacationDelegationService(user).activate(sub_ids)

    # Auto-stop: users past their end date
    for user in user_model.objects.filter(
        absence_status__in=[
            AbsenceStatus.VACATION,
            AbsenceStatus.SICK_LEAVE,
        ],
        vacation_end_date__isnull=False,
    ):
        user_now = now.astimezone(pytz_tz(user.timezone))
        if user_now.date() > user.vacation_end_date:
            VacationDelegationService(user).deactivate()
