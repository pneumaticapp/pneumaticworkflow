from datetime import datetime
from typing import Optional
from django.utils import timezone
from pneumatic_backend.accounts.enums import UserStatus
from pneumatic_backend.processes.enums import WorkflowStatus
from pneumatic_backend.queries import SqlQueryObject
from pneumatic_backend.processes.enums import DirectlyStatus
from pneumatic_backend.reports.queries.mixins import (
    TasksMixin,
    TasksNowMixin
)
from pneumatic_backend.processes.enums import TemplateType


class TasksOverviewQuery(
    TasksMixin,
    SqlQueryObject,
):
    def __init__(
        self,
        account_id: int,
        user_id: int,
        date_from: datetime,
        date_to: datetime,
        **kwargs
    ):
        self.params = {
            'account_id': account_id,
            'user_id': user_id,
            'date_from': date_from,
            'date_to': date_to,
            'status_done': WorkflowStatus.DONE,
            'type_user': TemplateType.CUSTOM,
            'type_generic': TemplateType.LIBRARY,
            'directly_status': DirectlyStatus.DELETED,
        }

    def get_sql(self):
        return f"""
        SELECT
          COUNT(pt.id) FILTER (
            {self._tasks_in_progress_clause()}
          ) AS in_progress,
          COUNT(pt.id) FILTER (
            {self._started_tasks_clause()}
          ) AS started,
          COUNT(pt.id) FILTER (
            {self._completed_tasks_clause()}
          ) AS completed,
          COUNT(pt.id) FILTER (
            {self._overdue_tasks_clause()}
          ) AS overdue
        FROM processes_task pt
        JOIN processes_taskperformer ptp ON pt.id = ptp.task_id
        JOIN processes_workflow pw ON pt.workflow_id = pw.id
        LEFT JOIN processes_template p on pw.template_id = p.id AND
        p.type IN (%(type_user)s, %(type_generic)s)
        WHERE
          pt.is_deleted IS FALSE AND
          ptp.user_id = %(user_id)s AND
          ptp.directly_status != %(directly_status)s AND
          pw.is_deleted IS FALSE AND
          pw.account_id = %(account_id)s
        """, self.params


class TasksOverviewNowQuery(
    TasksNowMixin,
    SqlQueryObject,
):
    def __init__(
        self,
        account_id: int,
        user_id: int,
    ):
        self.params = {
            'account_id': account_id,
            'user_id': user_id,
            'now': timezone.now(),
            'status_running': WorkflowStatus.RUNNING,
            'type_user': TemplateType.CUSTOM,
            'type_generic': TemplateType.LIBRARY,
            'directly_status': DirectlyStatus.DELETED,
        }

    def get_sql(self):
        return f"""
        SELECT
          COUNT(pt.id) FILTER (
            {self._tasks_in_progress_now_clause()}
          ) AS in_progress,
          NULL AS started,
          NULL AS completed,
          COUNT(pt.id) FILTER (
            {self._overdue_tasks_now_clause()}
          ) AS overdue
        FROM processes_task pt
        JOIN processes_taskperformer ptp ON pt.id = ptp.task_id
        JOIN processes_workflow pw ON pt.workflow_id = pw.id
        LEFT JOIN processes_template p on pw.template_id = p.id AND
        p.type IN (%(type_user)s, %(type_generic)s)
        WHERE
          pt.is_deleted IS FALSE AND
          ptp.user_id = %(user_id)s AND
          ptp.is_completed IS FALSE AND
          ptp.directly_status != %(directly_status)s AND
          pw.is_deleted IS FALSE AND
          pw.account_id = %(account_id)s
        """, self.params


class TasksBreakdownQuery(
    TasksMixin,
    SqlQueryObject,
):
    def __init__(
        self,
        account_id: int,
        user_id: int,
        date_from: datetime,
        date_to: datetime,
        **kwargs
    ):
        self.params = {
            'account_id': account_id,
            'user_id': user_id,
            'date_from': date_from,
            'date_to': date_to,
            'status_done': WorkflowStatus.DONE,
            'type_user': TemplateType.CUSTOM,
            'type_generic': TemplateType.LIBRARY,
            'directly_status': DirectlyStatus.DELETED,
        }

    def get_sql(self):
        return f"""
        SELECT
          ptmp.id AS template_id,
          ptmp.name AS template_name,
          COUNT(pt.id) FILTER (
            {self._tasks_in_progress_clause()}
          ) AS in_progress,
          COUNT(pt.id) FILTER (
            {self._started_tasks_clause()}
          ) AS started,
          COUNT(pt.id) FILTER (
            {self._completed_tasks_clause()}
          ) AS completed,
          COUNT(pt.id) FILTER (
            {self._overdue_tasks_clause()}
          ) AS overdue
        FROM processes_task pt
        JOIN processes_taskperformer ptp ON pt.id = ptp.task_id
        JOIN processes_workflow pw ON pt.workflow_id = pw.id
        JOIN processes_template ptmp ON pw.template_id = ptmp.id
        WHERE
          pt.is_deleted IS FALSE AND
          ptp.user_id = %(user_id)s AND
          ptp.directly_status != %(directly_status)s AND
          pw.is_deleted IS FALSE AND
          pw.account_id = %(account_id)s AND
          ptmp.is_deleted IS FALSE AND
          ptmp.type IN (%(type_user)s, %(type_generic)s)
        GROUP BY ptmp.id
        HAVING COUNT(pt.id) FILTER (
          {self._tasks_in_progress_clause()}
        ) > 0
        ORDER BY in_progress DESC, ptmp.id
        """, self.params


class TasksBreakdownNowQuery(
    TasksNowMixin,
    SqlQueryObject,
):
    def __init__(
        self,
        account_id: int,
        user_id: int,
    ):
        self.params = {
            'account_id': account_id,
            'user_id': user_id,
            'now': timezone.now(),
            'status_running': WorkflowStatus.RUNNING,
            'type_user': TemplateType.CUSTOM,
            'type_generic': TemplateType.LIBRARY,
            'directly_status': DirectlyStatus.DELETED,
        }

    def get_sql(self):
        return f"""
        SELECT
          ptmp.id AS template_id,
          ptmp.name AS template_name,
          COUNT(pt.id) FILTER (
            {self._tasks_in_progress_now_clause()}
          ) AS in_progress,
          NULL AS started,
          NULL AS completed,
          COUNT(pt.id) FILTER (
            {self._overdue_tasks_now_clause()}
          ) AS overdue
        FROM processes_task pt
        JOIN processes_taskperformer ptp ON pt.id = ptp.task_id
        JOIN processes_workflow pw ON pt.workflow_id = pw.id
        JOIN processes_template ptmp ON pw.template_id = ptmp.id
        WHERE
          pt.is_deleted IS FALSE AND
          ptp.user_id = %(user_id)s AND
          ptp.is_completed IS FALSE AND
          ptp.directly_status != %(directly_status)s AND
          pw.is_deleted IS FALSE AND
          pw.account_id = %(account_id)s AND
          ptmp.is_deleted IS FALSE AND
          ptmp.type IN (%(type_user)s, %(type_generic)s)
        GROUP BY ptmp.id
        HAVING COUNT(pt.id) FILTER (
          {self._tasks_in_progress_now_clause()}
        ) > 0
        ORDER BY in_progress DESC, ptmp.id
        """, self.params


class TasksBreakdownByStepsQuery(
    TasksMixin,
    SqlQueryObject,
):
    def __init__(
        self,
        user_id: int,
        template_id: int,
        date_from: datetime,
        date_to: datetime,
        **kwargs
    ):
        self.params = {
            'user_id': user_id,
            'template_id': template_id,
            'date_from': date_from,
            'date_to': date_to,
            'directly_status': DirectlyStatus.DELETED,
        }

    def get_sql(self):
        return f"""
        SELECT
          tt.id,
          tt.name,
          tt.number,
          COUNT(pt.id) FILTER (
            {self._tasks_in_progress_clause()}
          ) AS in_progress,
          COUNT(pt.id) FILTER (
            {self._started_tasks_clause()}
          ) AS started,
          COUNT(pt.id) FILTER (
            {self._completed_tasks_clause()}
          ) AS completed,
          COUNT(pt.id) FILTER (
            {self._overdue_tasks_clause()}
          ) AS overdue
        FROM processes_task pt
        JOIN processes_taskperformer ptp
          ON pt.id = ptp.task_id AND ptp.user_id = %(user_id)s
        JOIN processes_workflow pw ON pt.workflow_id = pw.id
        JOIN processes_tasktemplate tt ON pt.template_id = tt.id
        WHERE
          ptp.directly_status != %(directly_status)s AND
          pt.is_deleted IS FALSE AND
          tt.is_deleted IS FALSE AND
          tt.template_id = %(template_id)s AND
          pw.is_deleted IS FALSE
        GROUP BY tt.id, tt.number
        ORDER BY tt.number
        """, self.params


class TasksBreakdownByStepsNowQuery(
    TasksNowMixin,
    SqlQueryObject,
):
    def __init__(
        self,
        user_id: int,
        template_id: int,
    ):
        self.params = {
            'user_id': user_id,
            'template_id': template_id,
            'now': timezone.now(),
            'status_running': WorkflowStatus.RUNNING,
            'directly_status': DirectlyStatus.DELETED,
        }

    def get_sql(self):
        return f"""
        SELECT
          tt.id,
          tt.name,
          tt.number,
          COUNT(pt.id) FILTER (
            {self._tasks_in_progress_now_clause()}
          ) AS in_progress,
          NULL AS started,
          NULL AS completed,
          COUNT(pt.id) FILTER (
            {self._overdue_tasks_now_clause()}
          ) AS overdue
        FROM processes_task pt
        JOIN processes_taskperformer ptp
          ON pt.id = ptp.task_id AND ptp.user_id = %(user_id)s
        JOIN processes_workflow pw ON pt.workflow_id = pw.id
        JOIN processes_tasktemplate tt ON pt.template_id = tt.id
        WHERE
          pt.is_deleted IS FALSE AND
          tt.is_deleted IS FALSE AND
          tt.template_id = %(template_id)s AND
          pw.is_deleted IS FALSE AND
          ptp.is_completed IS FALSE AND
          ptp.directly_status != %(directly_status)s
        GROUP BY tt.id, tt.number
        ORDER BY tt.number
        """, self.params


class TasksDigestQuery(
    TasksMixin,
    SqlQueryObject,
):

    """ Returns the tasks statistic for all performers who have
        subscribed to the digest """

    def __init__(
        self,
        date_from: datetime,
        date_to: datetime,
        user_id: Optional[int],
        force=False,
    ):
        self._force = force
        self._user_id = user_id
        self.params = {
            'date_from': date_from,
            'date_to': date_to,
            'active_user': UserStatus.ACTIVE,
            'directly_status': DirectlyStatus.DELETED
        }
        self.template_types, template_types_params = self._to_sql_list(
            [TemplateType.CUSTOM, TemplateType.LIBRARY],
            'type'
        )
        self.params.update(template_types_params)

    def _get_subscriber_where(self):
        where = 'AND au.is_tasks_digest_subscriber IS TRUE '
        if not self._force:
            where += """
            AND (
              au.last_tasks_digest_send_time IS NULL OR
              au.last_tasks_digest_send_time < %(date_to)s - INTERVAL '6 DAY'
            )
            """
        return where

    def _get_user_where(self):
        where = ''
        if self._user_id is not None:
            where = 'AND au.id = %(user_id)s '
            self.params['user_id'] = self._user_id
        return where

    def get_sql(self):
        return f"""
        SELECT
          au.id AS user_id,
          ptmp.id AS template_id,
          ptmp.name AS template_name,
          tt.id AS template_task_id,
          tt.number,
          tt.name AS template_task_name,
          COUNT(pt.id) FILTER (
            {self._tasks_in_progress_clause()}
          ) AS in_progress,
          COUNT(pt.id) FILTER (
            {self._started_tasks_clause()}
          ) AS started,
          COUNT(pt.id) FILTER (
            {self._completed_tasks_clause()}
          ) AS completed,
          COUNT(pt.id) FILTER (
            {self._overdue_tasks_clause()}
          ) AS overdue
        FROM processes_task pt
        JOIN processes_taskperformer ptp ON pt.id = ptp.task_id
        JOIN processes_workflow pw ON pt.workflow_id = pw.id
        JOIN processes_template ptmp ON pw.template_id = ptmp.id
        JOIN processes_tasktemplate tt ON pt.template_id = tt.id
        JOIN accounts_user au ON ptp.user_id = au.id
        JOIN accounts_account aa ON au.account_id = aa.id
        WHERE
          ptmp.is_deleted IS FALSE AND
          ptmp.type IN {self.template_types} AND
          pt.is_deleted IS FALSE AND
          pw.is_deleted IS FALSE AND
          tt.is_deleted IS FALSE AND
          au.is_deleted IS FALSE AND
          au.status = %(active_user)s AND
          aa.payment_card_provided = TRUE AND
          ptp.directly_status != %(directly_status)s
          {self._get_subscriber_where()}
          {self._get_user_where()}
        GROUP BY au.id, ptmp.id, tt.id
        HAVING COUNT(DISTINCT pw.id) FILTER (
          {self._tasks_in_progress_clause()}
        ) > 0
        ORDER BY user_id, template_id, tt.number, in_progress DESC
        """, self.params
