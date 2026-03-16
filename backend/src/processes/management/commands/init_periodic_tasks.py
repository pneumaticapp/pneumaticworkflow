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

        tasks = [
            self._ensure_update_comment_watched,
            self._ensure_send_overdue_task_notifications,
            self._ensure_my_tasks_digest,
            self._ensure_send_system_notification,
            self._ensure_unread_notifications,
            self._ensure_weekly_digest,
            self._ensure_continue_delayed_processes,
            self._ensure_reminder_task_notification,
        ]

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
        if PeriodicTask.objects.filter(name=name).exists():
            self.stdout.write(
                self.style.WARNING(f"Task '{name}' already exists."),
            )
            return

        create_kwargs = {
            "name": name,
            "task": task_path,
            schedule_field: schedule_obj,
        }

        PeriodicTask.objects.create(**create_kwargs)
        self.stdout.write(
            self.style.SUCCESS(f"Task '{name}' has been created."),
        )

    # ──────────────────────────────────────────────
    #  Specific tasks
    # ──────────────────────────────────────────────

    def _ensure_update_comment_watched(self):
        name = 'Update comment "watched" counter'
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.SECONDS,
        )
        self._create_or_skip_task(
            name=name,
            task_path="src.notifications.tasks.send_workflow_comment_watched",
            schedule_obj=schedule,
        )

    def _ensure_send_overdue_task_notifications(self):
        name = "Send overdue task notifications"
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )
        self._create_or_skip_task(
            name=name,
            task_path="src.notifications.tasks.send_overdue_task_notification",
            schedule_obj=schedule,
        )

    def _ensure_my_tasks_digest(self):
        name = "My tasks digest"
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="8",
            day_of_week="5",
            timezone=pytz.timezone("US/Central"),
        )
        self._create_or_skip_task(
            name=name,
            task_path="src.reports.tasks.send_tasks_digest",
            schedule_obj=schedule,
            schedule_field="crontab",
        )

    def _ensure_send_system_notification(self):
        name = "Send System Notification"
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.MINUTES,
        )
        self._create_or_skip_task(
            name=name,
            task_path="src.accounts.tasks.send_system_notification",
            schedule_obj=schedule,
        )

    def _ensure_unread_notifications(self):
        name = "Unread notifications"
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )
        self._create_or_skip_task(
            name=name,
            task_path="src.notifications.tasks.send_unread_notifications",
            schedule_obj=schedule,
        )

    def _ensure_weekly_digest(self):
        name = "Weekly Digest"
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="11",
            day_of_week="1",
            timezone=pytz.timezone("US/Central"),
        )
        self._create_or_skip_task(
            name=name,
            task_path="src.reports.tasks.send_digest",
            schedule_obj=schedule,
            schedule_field="crontab",
        )

    def _ensure_continue_delayed_processes(self):
        name = "continue_delayed_processes"
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="*/1",
            timezone=pytz.timezone("UTC"),
        )
        self._create_or_skip_task(
            name=name,
            task_path="src.processes.tasks.delay.continue_delayed_workflows",
            schedule_obj=schedule,
            schedule_field="crontab",
        )

    def _ensure_reminder_task_notification(self):
        name = "Reminder task notification"
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )
        self._create_or_skip_task(
            name=name,
            task_path=(
                "src.notifications.tasks.send_reminder_task_notification"
            ),
            schedule_obj=schedule,
        )
