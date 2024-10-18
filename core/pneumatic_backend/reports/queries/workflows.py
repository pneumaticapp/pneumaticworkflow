from datetime import datetime
from typing import Optional

from django.utils import timezone
from pneumatic_backend.processes.enums import TemplateType
from pneumatic_backend.accounts.enums import UserStatus
from pneumatic_backend.processes.enums import WorkflowStatus
from pneumatic_backend.queries import SqlQueryObject
from pneumatic_backend.reports.queries.mixins import (
    WorkflowsMixin,
    WorkflowsNowMixin,
    WorkflowTasksMixin,
    WorkflowTasksNowMixin
)


class OverviewQuery(
    WorkflowsMixin,
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
            'type_user': TemplateType.CUSTOM,
            'type_generic': TemplateType.LIBRARY,
        }

    def get_sql(self):
        return f"""
        WITH overdue_workflows AS (
            {self._overdue_workflows_cte()}
        )
        SELECT
          COUNT(DISTINCT pw.id) FILTER (
            {self._workflows_in_progress_clause()}
          ) AS in_progress,
          COUNT(DISTINCT pw.id) FILTER (
            {self._started_workflows_clause()}
          ) AS started,
          COUNT(DISTINCT pw.id) FILTER (
            {self._completed_workflows_clause()}
          ) AS completed,
          COUNT(DISTINCT pw.id) FILTER (
            {self._overdue_workflows_clause()}
          ) AS overdue
        FROM processes_workflow pw
        LEFT JOIN processes_template pt ON pw.template_id = pt.id AND
          pt.is_deleted IS FALSE AND
          pt.type IN (%(type_user)s, %(type_generic)s)
        LEFT JOIN
          processes_template_template_owners ptra ON pt.id = ptra.template_id
        LEFT JOIN overdue_workflows ow ON pw.id = ow.workflow_id
        WHERE pw.account_id = %(account_id)s AND
          pw.is_deleted IS FALSE AND
          (
            (
              pw.is_legacy_template IS TRUE AND
              pw.workflow_starter_id = %(user_id)s
            ) OR
            ptra.user_id = %(user_id)s
          )
        """, self.params


class OverviewNowQuery(
    WorkflowsNowMixin,
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
        }

    def get_sql(self):
        return f"""
        WITH overdue_workflows AS (
            {self._overdue_workflows_now_cte()}
        )
        SELECT
          COUNT(DISTINCT pw.id) FILTER (
            {self._workflows_in_progress_now_clause()}
          ) AS in_progress,
          NULL AS started,
          NULL AS completed,
          COUNT(DISTINCT pw.id) FILTER (
            {self._overdue_workflows_now_clause()}
          ) AS overdue
        FROM processes_workflow pw
        LEFT JOIN processes_template pt ON pw.template_id = pt.id AND
          pt.is_deleted IS FALSE AND
          pt.type IN (%(type_user)s, %(type_generic)s)
        LEFT JOIN
          processes_template_template_owners ptra ON pt.id = ptra.template_id
        LEFT JOIN overdue_workflows ow ON pw.id = ow.workflow_id
        WHERE pw.account_id = %(account_id)s AND
          pw.is_deleted IS FALSE AND
          pw.status = %(status_running)s AND (
            (
              pw.is_legacy_template IS TRUE AND
              pw.workflow_starter_id = %(user_id)s
            ) OR
            ptra.user_id = %(user_id)s
          )
        """, self.params


class WorkflowBreakdownQuery(
    WorkflowsMixin,
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
            'type_user': TemplateType.CUSTOM,
            'type_generic': TemplateType.LIBRARY,
        }

    def get_sql(self):
        return f"""
        WITH overdue_workflows AS (
          {self._overdue_workflows_cte()}
        )
        SELECT
          pt.id AS template_id,
          pt.name AS template_name,
          pt.is_active,
          COUNT(DISTINCT pw.id) FILTER (
            {self._workflows_in_progress_clause()}
          ) AS in_progress,
          COUNT(DISTINCT pw.id) FILTER (
            {self._started_workflows_clause()}
          ) AS started,
          COUNT(DISTINCT pw.id) FILTER (
            {self._completed_workflows_clause()}
          ) AS completed,
          COUNT(DISTINCT pw.id) FILTER (
            {self._overdue_workflows_clause()}
          ) AS overdue
        FROM processes_template pt
        LEFT JOIN processes_workflow pw ON pw.template_id = pt.id AND
          pw.is_deleted IS FALSE
        JOIN processes_template_template_owners ptra
          ON pt.id = ptra.template_id
        LEFT JOIN overdue_workflows ow ON pw.id = ow.workflow_id
        WHERE pt.account_id = %(account_id)s AND
          pt.is_deleted IS FALSE AND
          pt.type IN (%(type_user)s, %(type_generic)s) AND
          ptra.user_id = %(user_id)s
        GROUP BY pt.id
        ORDER BY in_progress DESC, template_id
        """, self.params


class WorkflowBreakdownNowQuery(
    WorkflowsNowMixin,
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
        }

    def get_sql(self):
        return f"""
        WITH overdue_workflows AS (
          {self._overdue_workflows_now_cte()}
        )
        SELECT
          pt.id AS template_id,
          pt.name AS template_name,
          pt.is_active,
          COUNT(DISTINCT pw.id) FILTER (
            {self._workflows_in_progress_now_clause()}
          ) AS in_progress,
          NULL AS started,
          NULL AS completed,
          COUNT(DISTINCT pw.id) FILTER (
            {self._overdue_workflows_now_clause()}
          ) AS overdue
        FROM processes_template pt
        LEFT JOIN processes_workflow pw ON pw.template_id = pt.id AND
          pw.is_deleted IS FALSE AND
          pw.status = %(status_running)s
        JOIN processes_template_template_owners ptra
          ON pt.id = ptra.template_id
        LEFT JOIN overdue_workflows ow ON pw.id = ow.workflow_id
        WHERE pt.account_id = %(account_id)s AND
          pt.is_deleted IS FALSE AND
          pt.type IN (%(type_user)s, %(type_generic)s) AND
          ptra.user_id = %(user_id)s
        GROUP BY pt.id
        ORDER BY in_progress DESC, template_id
        """, self.params


class WorkflowDigestQuery(
    WorkflowsMixin,
    SqlQueryObject,
):

    """ Returns the workflows statistic for all template owners who have
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
            'active_user': UserStatus.ACTIVE
        }
        self.template_types, template_types_params = self._to_sql_list(
            [TemplateType.CUSTOM, TemplateType.LIBRARY],
            'type'
        )
        self.params.update(template_types_params)

    def _get_subscriber_where(self):
        where = 'AND au.is_digest_subscriber IS TRUE '
        if not self._force:
            where += """
            AND (
              au.last_digest_send_time IS NULL OR
              au.last_digest_send_time < %(date_to)s
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
        WITH overdue_workflows AS (
          {self._overdue_workflows_cte()}
        )
        SELECT
          au.id AS user_id,
          pt.id AS template_id,
          pt.name AS template_name,
          COUNT(DISTINCT pw.id) FILTER (
            {self._workflows_in_progress_clause()}
          ) AS in_progress,
          COUNT(DISTINCT pw.id) FILTER (
            {self._started_workflows_clause()}
          ) AS started,
          COUNT(DISTINCT pw.id) FILTER (
            {self._completed_workflows_clause()}
          ) AS completed,
          COUNT(DISTINCT pw.id) FILTER (
            {self._overdue_workflows_clause()}
          ) AS overdue
        FROM processes_template pt
        JOIN processes_template_template_owners ptra
          ON pt.id = ptra.template_id
        JOIN accounts_user au ON ptra.user_id = au.id
        JOIN accounts_account aa ON au.account_id = aa.id
        JOIN processes_workflow pw ON pt.id = pw.template_id
        LEFT JOIN overdue_workflows ow ON pw.id = ow.workflow_id
        WHERE
          pt.is_deleted IS FALSE AND
          pt.type IN {self.template_types} AND
          pw.is_deleted IS FALSE AND
          au.is_deleted IS FALSE AND
          au.status = %(active_user)s AND
          aa.payment_card_provided=True
          {self._get_subscriber_where()}
          {self._get_user_where()}
        GROUP BY au.id, pt.id
        HAVING COUNT(DISTINCT pw.id) FILTER (
          WHERE pw.date_created <= %(date_to)s AND
          (pw.date_completed IS NULL OR pw.date_completed >= %(date_from)s)
        ) > 0
        ORDER BY au.id, in_progress DESC, template_id
        """, self.params


class WorkflowBreakdownByTasksQuery(
    WorkflowTasksMixin,
    SqlQueryObject,
):

    """ Returns statistics for each template task

        * SQL CTE-query used to retrieve default statistics values
        when template workflows are not found
    """

    def __init__(
        self,
        template_id: int,
        date_from: datetime,
        date_to: datetime,
        **kwargs
    ):
        self.params = {
            'template_id': template_id,
            'date_from': date_from,
            'date_to': date_to,
        }

    def get_sql(self):
        return f"""
        WITH
          template_tasks AS (
            SELECT
              id,
              name,
              number
            FROM processes_tasktemplate
            WHERE is_deleted IS FALSE
              AND template_id = %(template_id)s
          ),
          results AS (
            SELECT
              tt.id,
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
            FROM template_tasks tt
            JOIN processes_task pt
              ON pt.template_id = tt.id
              AND pt.is_deleted IS FALSE
            JOIN processes_workflow pw
              ON pt.workflow_id = pw.id
              AND pw.is_deleted IS FALSE
            GROUP BY tt.id
          )

        SELECT
          tasks.id,
          tasks.name,
          tasks.number,
          COALESCE(results.in_progress, 0) AS in_progress,
          COALESCE(results.started, 0) AS started,
          COALESCE(results.completed, 0) AS completed,
          COALESCE(results.overdue, 0) AS overdue
        FROM template_tasks tasks
          LEFT JOIN results ON tasks.id = results.id
        ORDER BY tasks.number
        """, self.params


class WorkflowBreakdownByTasksNowQuery(
    WorkflowTasksNowMixin,
    SqlQueryObject,
):
    def __init__(
        self,
        template_id: int,
    ):
        self.params = {
            'template_id': template_id,
            'now': timezone.now(),
            'status_running': WorkflowStatus.RUNNING,
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
        JOIN processes_workflow pw ON pt.workflow_id = pw.id
        JOIN processes_tasktemplate tt ON pt.template_id = tt.id
        WHERE
          pt.is_deleted IS FALSE AND
          tt.is_deleted IS FALSE AND
          tt.template_id = %(template_id)s AND
          pw.is_deleted IS FALSE
        GROUP BY tt.id, tt.number
        ORDER BY tt.number
        """, self.params
