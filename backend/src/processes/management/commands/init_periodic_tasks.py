from django.core.management.base import BaseCommand
from django_celery_beat.models import (
    PeriodicTask,
    IntervalSchedule,
    CrontabSchedule,
)
import pytz


class Command(BaseCommand):
    help = 'Initialize the system on startup'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("Starting system initialization..."),
        )
        self._setup_periodic_tasks()
        self.stdout.write(
            self.style.SUCCESS("System initialization complete."),
        )

    def _setup_periodic_tasks(self):
        """Creates all necessary periodic tasks if they do not exist yet."""
        self.stdout.write(self.style.SUCCESS("Setting up periodic tasks..."))

        tasks = (
            self._ensure_update_comment_watched,
            self._ensure_send_overdue_task_notifications,
            self._ensure_my_tasks_digest,
            self._ensure_send_system_notification,
            self._ensure_unread_notifications,
            self._ensure_weekly_digest,
            self._ensure_continue_delayed_processes,
            self._ensure_reminder_task_notification,
            self._ensure_process_vacation_schedules,
            self._ensure_delegate_vacation_tasks,
        )

        for task_func in tasks:
            task_func()

    def _create_or_skip_task(
        self,
        name: str,
        task_path: str,
        schedule_obj,
        schedule_field: str = "interval",
    ) -> None:
        """
        Universal method to create a PeriodicTask if it doesn't already exist.
        """
        if PeriodicTask.objects.filter(task=task_path).exists():
            return

        PeriodicTask.objects.create(
            name=name,
            task=task_path,
            **{schedule_field: schedule_obj},
        )
        self.stdout.write(
            self.style.SUCCESS(f"Task '{name}' has been created."),
        )

    # ──────────────────────────────────────────────
    #  Specific tasks
    # ──────────────────────────────────────────────

    def _ensure_update_comment_watched(self):
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.SECONDS,
        )
        self._create_or_skip_task(
            name='Update comment "watched" counter',
            task_path="src.notifications.tasks.send_workflow_comment_watched",
            schedule_obj=schedule,
        )

    def _ensure_send_overdue_task_notifications(self):
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )
        self._create_or_skip_task(
            name="Send overdue task notifications",
            task_path="src.notifications.tasks.send_overdue_task_notification",
            schedule_obj=schedule,
        )

    def _ensure_my_tasks_digest(self):
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="8",
            day_of_week="5",
            timezone=pytz.timezone("US/Central"),
        )
        self._create_or_skip_task(
            name="My tasks digest",
            task_path="src.reports.tasks.send_tasks_digest",
            schedule_obj=schedule,
            schedule_field="crontab",
        )

    def _ensure_send_system_notification(self):
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.MINUTES,
        )
        self._create_or_skip_task(
            name="Send System Notification",
            task_path="src.accounts.tasks.send_system_notification",
            schedule_obj=schedule,
        )

    def _ensure_unread_notifications(self):
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )
        self._create_or_skip_task(
            name="Unread notifications",
            task_path="src.notifications.tasks.send_unread_notifications",
            schedule_obj=schedule,
        )

    def _ensure_weekly_digest(self):
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="11",
            day_of_week="1",
            timezone=pytz.timezone("US/Central"),
        )
        self._create_or_skip_task(
            name="Weekly Digest",
            task_path="src.reports.tasks.send_digest",
            schedule_obj=schedule,
            schedule_field="crontab",
        )

    def _ensure_continue_delayed_processes(self):
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="*/1",
            timezone=pytz.timezone("UTC"),
        )
        self._create_or_skip_task(
            name="continue_delayed_processes",
            task_path="src.processes.tasks.delay.continue_delayed_workflows",
            schedule_obj=schedule,
            schedule_field="crontab",
        )

    def _ensure_reminder_task_notification(self):
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )
        self._create_or_skip_task(
            name="Reminder task notification",
            task_path=(
                "src.notifications.tasks.send_reminder_task_notification"
            ),
            schedule_obj=schedule,
        )

    def _ensure_process_vacation_schedules(self):
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="*/15",
            timezone=pytz.timezone("UTC"),
        )
        self._create_or_skip_task(
            name="Process vacation schedules",
            task_path=(
                "src.accounts.tasks.process_vacation_schedules"
            ),
            schedule_obj=schedule,
            schedule_field="crontab",
        )

    def _ensure_delegate_vacation_tasks(self):
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="*/5",
            timezone=pytz.timezone("UTC"),
        )
        self._create_or_skip_task(
            name="Delegate vacation tasks",
            task_path=(
                "src.processes.tasks.tasks.delegate_vacation_tasks"
            ),
            schedule_obj=schedule,
            schedule_field="crontab",
        )
