from pytz import timezone as pytz_tz
from pytz.exceptions import UnknownTimeZoneError
from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from src.accounts.enums import AbsenceStatus
from src.accounts.models import (
    Notification,
    SystemMessage,
)
from src.accounts.queries import CreateSystemNotificationsQuery
from src.accounts.services.vacation import VacationDelegationService
from src.executor import RawSqlExecutor
from src.notifications.enums import NotificationMethod
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


@shared_task
def process_vacations():
    """Auto-start and auto-stop vacation delegations.

    Runs every 15 minutes via Celery beat.
    Checks user timezones to determine if vacation should
    start or end based on local date.
    Per-user error isolation ensures one failure does not
    block processing of other users.
    """
    user_model = get_user_model()
    now = timezone.now()

    auto_start_users = (
        user_model.objects
        .filter(
            vacations__isnull=False,
            vacations__is_deleted=False,
            vacations__absence_status=AbsenceStatus.ACTIVE,
            vacations__start_date__isnull=False,
            vacations__substitute_group__isnull=False,
        )
        .order_by('id')
    )
    for user in auto_start_users:
        try:
            user_now = now.astimezone(pytz_tz(user.timezone))
        except UnknownTimeZoneError:
            continue
        vacation = user.vacation
        if not vacation:
            continue
        if user_now.date() >= vacation.start_date:
            sub_ids = list(
                vacation.substitute_group.users
                .values_list('id', flat=True),
            )
            if sub_ids:
                try:
                    VacationDelegationService(user).activate(
                        sub_ids,
                        absence_status=AbsenceStatus.VACATION,
                        vacation_start_date=(
                            vacation.start_date
                        ),
                        vacation_end_date=(
                            vacation.end_date
                        ),
                    )
                except Exception:  # noqa: BLE001
                    continue

    # Auto-stop: users past their end date
    auto_stop_users = (
        user_model.objects
        .filter(
            vacations__isnull=False,
            vacations__is_deleted=False,
            vacations__absence_status__in=[
                AbsenceStatus.VACATION,
                AbsenceStatus.SICK_LEAVE,
            ],
            vacations__end_date__isnull=False,
        )
        .order_by('id')
    )
    for user in auto_stop_users:
        try:
            user_now = now.astimezone(pytz_tz(user.timezone))
        except UnknownTimeZoneError:
            continue
        vacation = user.vacation
        if vacation and user_now.date() > vacation.end_date:
            try:
                VacationDelegationService(user).deactivate()
            except Exception:  # noqa: BLE001
                continue
