from collections import defaultdict
from dataclasses import asdict
from datetime import timedelta
from typing import Dict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from src.executor import RawSqlExecutor
from src.reports.entities import (
    TemplateForWorkflowsDigest,
    WorkflowsDigest,
)
from src.reports.queries.workflows import (
    WorkflowDigestQuery,
)
from src.reports.services.base import (
    SendDigest,
)
from src.notifications.tasks import send_workflows_digest_notification

UserModel = get_user_model()


class SendWorkflowsDigest(SendDigest):

    def __init__(self, user_id=None, force=False, fetch_size=50):
        super().__init__(user_id, force)
        self._fetch_size = fetch_size
        self._now = timezone.now()
        current_week_monday = (
            self._now - timedelta(days=self._now.weekday())
        ).date()
        self._date_from = current_week_monday - timedelta(days=7)
        self._date_to = current_week_monday

    def _fetch_data(self):
        query = WorkflowDigestQuery(
            date_from=self._date_from,
            date_to=self._date_to,
            user_id=self._user_id,
            force=self._force,
        )
        return RawSqlExecutor.fetch(
            *query.get_sql(),
            stream=True,
            fetch_size=self._fetch_size,
            db=settings.REPLICA,
        )

    def _add_user_data(self, user_digest: WorkflowsDigest, row):
        user_digest.started += row['started']
        user_digest.in_progress += row['in_progress']
        user_digest.overdue += row['overdue']
        user_digest.completed += row['completed']
        user_digest.templates.append(
            TemplateForWorkflowsDigest(
                template_id=row['template_id'],
                template_name=row['template_name'],
                started=row['started'],
                in_progress=row['in_progress'],
                overdue=row['overdue'],
                completed=row['completed'],
            ),
        )

    def _send_emails(self, digests: Dict[int, WorkflowsDigest]):
        users = UserModel.objects.select_related(
            'account',
        ).by_ids(list(digests.keys()))
        for user in users:
            digest = digests.get(user.id)
            if digest:
                send_workflows_digest_notification.delay(
                    user_id=user.id,
                    user_email=user.email,
                    account_id=user.account_id,
                    date_from=self._date_from.strftime('%d %b'),
                    date_to=(
                        (self._date_to - timedelta(days=1))
                        .strftime('%d %b, %Y')
                    ),
                    digest=asdict(digest),
                    logo_lg=user.account.logo_lg,
                )
                user.last_digest_send_time = self._now
                user.save(update_fields=['last_digest_send_time'])
                self._sent_digests_count += 1

    def _process_data(self, data, bulk_size=10):
        users_count = 0
        user_id = None
        digests = defaultdict(WorkflowsDigest)
        for row in data:
            if row['user_id'] != user_id:
                user_id = row['user_id']
                users_count += 1
                if users_count > bulk_size:
                    self._send_emails(digests)
                    digests = defaultdict(WorkflowsDigest)
                    users_count = 1
            self._add_user_data(digests[user_id], row)

        if digests:
            self._send_emails(digests)
