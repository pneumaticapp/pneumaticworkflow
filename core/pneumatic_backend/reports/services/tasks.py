from collections import defaultdict
from dataclasses import asdict
from datetime import timedelta
from typing import Dict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from pneumatic_backend.executor import RawSqlExecutor
from pneumatic_backend.processes.utils.common import (
    VAR_PATTERN,
    insert_fields_values_to_text,
)
from pneumatic_backend.reports.entities import (
    TasksDigest,
    TemplateForTasksDigest,
    TaskForTasksDigest,
)
from pneumatic_backend.reports.services.base import (
    SendDigest,
)
from pneumatic_backend.reports.queries.tasks import (
    TasksDigestQuery,
)
from pneumatic_backend.services.email import EmailService


UserModel = get_user_model()


class SendTasksDigest(SendDigest):

    def __init__(self, user_id=None, force=None, fetch_size=50):
        super().__init__(user_id, force)
        self._now = timezone.now()
        self._date_from = self._now.date() - timedelta(days=7)
        self._date_to = self._now
        self._fetch_size = fetch_size

    def _fetch_data(self):
        query = TasksDigestQuery(
            date_from=self._date_from,
            date_to=self._date_to,
            user_id=self._user_id,
            force=self._force,
        )
        sql, params = query.get_sql()
        data = RawSqlExecutor.fetch(
            sql,
            params,
            stream=True,
            fetch_size=self._fetch_size,
            db=settings.REPLICA,
        )
        return data

    def _replace_api_name(
        self,
        task_name: str,
        template: TemplateForTasksDigest,
    ):
        api_name = VAR_PATTERN.findall(task_name)
        if api_name:
            task_name = insert_fields_values_to_text(
                text=task_name,
                fields_values={api_name[0]: template.fields[api_name[0]]}
            )
        return task_name

    def _add_template_data(
        self,
        user_digest: TasksDigest,
        row,
    ):
        if (
            not user_digest.tmp or
            user_digest.tmp.template_id != row['template_id']
        ):
            user_digest.put_tmp()
            user_digest.tmp = TemplateForTasksDigest(
                template_id=row['template_id'],
                template_name=row['template_name'],
            )
        user_digest.tmp.started += row['started']
        user_digest.tmp.in_progress += row['in_progress']
        user_digest.tmp.overdue += row['overdue']
        user_digest.tmp.completed += row['completed']
        task_name = self._replace_api_name(
            row['template_task_name'],
            user_digest.tmp,
        )
        user_digest.tmp.tasks.append(
            TaskForTasksDigest(
                task_id=row['template_task_id'],
                task_name=task_name,
                started=row['started'],
                in_progress=row['in_progress'],
                overdue=row['overdue'],
                completed=row['completed'],
            )
        )

    def _add_user_data(self, user_digest: TasksDigest, row):
        self._add_template_data(user_digest, row)
        user_digest.started += row['started']
        user_digest.in_progress += row['in_progress']
        user_digest.overdue += row['overdue']
        user_digest.completed += row['completed']

    def _send_emails(self, digests: Dict[int, TasksDigest]):
        users = UserModel.objects.select_related(
            'account'
        ).by_ids(list(digests.keys()))
        for user in users:
            digest = digests.get(user.id)

            if digest:
                EmailService.send_tasks_digest_email(
                    user=user,
                    date_to=self._date_to - timedelta(days=1),
                    date_from=self._date_from,
                    digest=asdict(digest),
                    logo_lg=user.account.logo_lg
                )
                user.last_tasks_digest_send_time = self._now
                user.save(update_fields=['last_tasks_digest_send_time'])
                self._sent_digests_count += 1

    def _process_data(self, data, bulk_size=10):
        users_count = 0
        user_id = None
        digests = defaultdict(TasksDigest)
        for row in data:
            if row['user_id'] != user_id:
                if user_id is not None:
                    digests[user_id].templates.sort(
                        key=lambda x: x.in_progress,
                        reverse=True,
                    )
                user_id = row['user_id']
                users_count += 1
                if users_count > bulk_size:
                    self._send_emails(digests)
                    digests = defaultdict(TasksDigest)
                    users_count = 1
            self._add_user_data(digests[user_id], row)

        if digests:
            digests[user_id].put_tmp()
            digests[user_id].templates.sort(
                key=lambda x: x.in_progress,
                reverse=True,
            )
            self._send_emails(digests)
