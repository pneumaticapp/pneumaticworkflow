from ast import literal_eval
from typing import Optional, List, Tuple
from datetime import datetime
from django.contrib.auth import get_user_model
from pneumatic_backend.accounts.models import User
from pneumatic_backend.generics.mixins.managers import SearchSqlQueryMixin
from pneumatic_backend.queries import (
    SqlQueryObject,
    OrderByMixin,
)
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    WorkflowApiStatus,
    WorkflowOrdering,
    DirectlyStatus,
    WorkflowEventType,
)
from pneumatic_backend.processes.enums import (
    TemplateOrdering,
    TaskOrdering,
    TemplateType,
)
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0022,
    MSG_PW_0024,
)

UserModel = get_user_model()


class WorkflowListQuery(
    SqlQueryObject,
    SearchSqlQueryMixin,
    OrderByMixin,
):
    ordering_map = WorkflowOrdering.MAP

    def __init__(
        self,
        account_id: int,
        user_id: int,
        status: Optional[str] = None,
        ordering: Optional[WorkflowOrdering.LITERALS] = None,
        template: Optional[List[int]] = None,
        template_task: Optional[List[int]] = None,
        current_performer: Optional[List[int]] = None,
        workflow_starter: Optional[List[int]] = None,
        is_external: Optional[bool] = None,
        search: Optional[str] = None,
    ):
        self.status = WorkflowApiStatus.MAP[status] if status else None
        self.params = {
            'account_id': account_id,
            'user_id': user_id,
            'directly_status': DirectlyStatus.DELETED,
            'status': self.status
        }
        self.ordering = ordering
        self.template = template
        self.template_task = template_task
        self.current_performer = current_performer
        self.workflow_starter = workflow_starter
        self.is_external = is_external
        self.search_text = search

    def _get_search(self):
        tsquery, params = self._get_tsquery()
        self.params.update(params)
        return f"""
            (
              {self._search_in(table='pt', tsquery=tsquery)}
              OR {self._search_in(table='pw', tsquery=tsquery)}
              OR {self._search_in(table='we', tsquery=tsquery)}
              OR {self._search_in(table='t', tsquery=tsquery)}
              OR {self._search_in(table='fa', tsquery=tsquery)}
              OR {self._search_in(table='ptf', tsquery=tsquery)}
              OR {self._search_in(table='kv', tsquery=tsquery)}
            )
        """

    def _get_template(self):
        result, params = self._to_sql_list(
            values=self.template,
            prefix='template'
        )
        self.params.update(params)
        return f"pw.template_id in {result}"

    def _get_template_task(self):
        result, params = self._to_sql_list(
            values=self.template_task,
            prefix='template_task'
        )
        self.params.update(params)
        return f"pt.template_id in {result}"

    def _get_current_performer(self):
        result, params = self._to_sql_list(
            values=self.current_performer,
            prefix='current_performer'
        )
        self.params.update(params)
        return f"ptp.user_id in {result}"

    def _get_workflow_starter(self):
        result, params = self._to_sql_list(
            values=self.workflow_starter,
            prefix='workflow_starter'
        )
        self.params.update(params)
        return f"pw.workflow_starter_id in {result}"

    def _get_is_external(self):
        self.params.update({'is_external': self.is_external})
        return """pw.is_external = %(is_external)s"""

    def _get_inner_where(self):
        where = f"""
            WHERE pw.is_deleted IS FALSE
            AND pw.account_id = %(account_id)s
            AND (
              pto.user_id = %(user_id)s
              OR pw.workflow_starter_id = %(user_id)s
            )
        """

        if self.template:
            where = f'{where} AND {self._get_template()}'

        if self.template_task:
            where = f'{where} AND {self._get_template_task()}'

        if self.current_performer:
            where = (
                f'{where} AND {self._get_current_performer()} '
                f'AND ptp.directly_status != %(directly_status)s '
            )
        if self.workflow_starter and self.is_external:
            where = (
                f'{where} AND ('
                f'{self._get_workflow_starter()} OR {self._get_is_external()})'
            )
        elif self.workflow_starter:
            where = f'{where} AND {self._get_workflow_starter()}'

        elif self.is_external is not None:
            where = f'{where} AND {self._get_is_external()}'

        if self.search_text:
            where = f'{where} AND {self._get_search()}'

        if self.status is not None:
            where = f'{where} AND pw.status = %(status)s'

        return where

    def _get_tables(self):
        result = """
            FROM processes_workflow pw
            INNER JOIN processes_task pt ON (
                pw.id = pt.workflow_id
                AND pt.number = pw.current_task
                AND pt.is_deleted IS FALSE
            )
            LEFT JOIN processes_delay pd
              ON pt.id = pd.task_id
                AND pw.status = 3
                AND pd.end_date IS NULL
                AND pd.is_deleted IS FALSE
            LEFT JOIN processes_template t ON (
                t.id = pw.template_id AND
                t.is_deleted IS FALSE
            )
            LEFT JOIN processes_template_template_owners pto ON (
                t.id = pto.template_id
            )
        """
        if self.current_performer:
            result += """
                LEFT JOIN processes_taskperformer ptp ON (
                    pt.id = ptp.task_id
                )
            """
        if self.search_text:
            result += """
                LEFT JOIN processes_kickoffvalue kv ON pw.id = kv.workflow_id
                LEFT JOIN processes_workflowevent we ON (
                    pw.id = we.workflow_id AND
                    we.is_deleted IS FALSE AND
                    we.status != 'deleted' AND
                    we.type = 5
                )
                LEFT JOIN processes_fileattachment fa ON (
                    pw.id=fa.workflow_id AND
                    fa.is_deleted is FALSE
                )
                LEFT JOIN processes_taskfield ptf ON (
                    ptf.workflow_id = pw.id AND
                    ptf.is_deleted IS FALSE
                )
            """
        return result

    def _get_inner_sql(self):
        tables = self._get_tables()
        where = self._get_inner_where()
        return f"""
            SELECT DISTINCT ON (pw.id)
                pw.id,
                pw.name,
                pw.template_id,
                pw.status,
                pw.tasks_count,
                pw.current_task,
                pw.is_legacy_template,
                pw.legacy_template_name,
                pw.is_external,
                pw.is_urgent,
                pw.date_created,
                pw.status_updated,
                pw.due_date,
                pw.workflow_starter_id,
                pw.finalizable,
                pt.id AS task_id,
                pt.name AS task_name,
                pt.number AS task_number,
                pt.due_date AS task_due_date,
                LEAST(pt.due_date, pw.due_date) AS nearest_due_date,
                pt.date_started AS task_date_started,
                pt.checklists_total AS task_checklists_total,
                pt.checklists_marked AS task_checklists_marked,
                pd.duration AS delay_duration,
                pd.start_date AS delay_start_date,
                pd.end_date AS delay_end_date,
                pd.estimated_end_date AS delay_estimated_end_date,
                t.id AS template_id,
                t.name AS template_name,
                t.is_active AS template_is_active
            {tables}
            {where}
            ORDER BY pw.id
        """

    def get_sql(self):
        inner_sql = self._get_inner_sql()
        post_columns = None
        default_column = 'workflows.date_created DESC'
        if self.ordering == WorkflowOrdering.URGENT_FIRST:
            post_columns = default_column
        order_by = self.get_order_by(
            default_column=default_column,
            post_columns=post_columns
        )
        return f"""
            SELECT *
            FROM ({inner_sql}) AS workflows
            {order_by}
        """, self.params


class WorkflowCountsByWfStarterQuery(
    SqlQueryObject
):

    def __init__(
        self,
        user_id: int,
        account_id: int,
        status: Optional[str] = None,
        template_ids: Optional[List[int]] = None,
        current_performer_ids: Optional[List[int]] = None,
    ):
        self.status = WorkflowApiStatus.MAP[status] if status else None
        self.params = {
            'user_id': user_id,
            'account_id': account_id,
            'directly_status': DirectlyStatus.DELETED,
            'status': self.status
        }
        self.template_ids = template_ids
        self.current_performer_ids = current_performer_ids

    def _get_template_ids(self):
        result, params = self._to_sql_list(
            values=self.template_ids,
            prefix='template_id'
        )
        self.params.update(params)
        return f"pw.template_id IN {result}"

    def _get_current_performer_ids(self):
        result, params = self._to_sql_list(
            values=self.current_performer_ids,
            prefix='current_performer_id'
        )
        self.params.update(params)
        return f"ptp.user_id in {result}"

    def _get_inner_where(self):
        where = """
            WHERE au.is_deleted IS FALSE
            AND pw.is_deleted IS FALSE
            AND pw.account_id = %(account_id)s
            AND ptra.user_id = %(user_id)s """

        if self.template_ids:
            where = f'{where} AND {self._get_template_ids()}'

        if self.current_performer_ids:
            where = (
                f'{where} AND {self._get_current_performer_ids()} '
                f'AND ptp.directly_status != %(directly_status)s '
                f'AND pt.is_deleted IS FALSE '
            )
        if self.status is not None:
            where = f'{where} AND pw.status = %(status)s'

        return where

    def _get_from(self):
        result = """
        FROM processes_workflow pw
            LEFT JOIN processes_template t ON t.id = pw.template_id
            LEFT JOIN processes_template_template_owners ptra
              ON t.id = ptra.template_id
            LEFT JOIN accounts_user au ON au.id = ptra.user_id
        """
        if self.current_performer_ids:
            result += """
            INNER JOIN processes_task pt
              ON (pw.id = pt.workflow_id AND pw.current_task = pt.number)
            INNER JOIN processes_taskperformer ptp
              ON pt.id = ptp.task_id
        """
        return result

    def _get_inner_sql(self):
        return f"""
        WITH main AS (
            SELECT
              DISTINCT pw.id AS workflow_id,
              pw.workflow_starter_id,
              pw.is_external
            {self._get_from()}
            {self._get_inner_where()}
        )
        SELECT
              -1 AS user_id,
              COUNT(workflow_id) AS workflows_count
            FROM main
            WHERE is_external IS TRUE
        UNION
        SELECT
              workflow_starter_id AS user_id,
              COUNT(workflow_id) AS workflows_count
            FROM main
            WHERE is_external IS FALSE
            GROUP BY user_id
        ORDER BY user_id ASC
        """

    def get_sql(self):
        sql = self._get_inner_sql()
        return sql, self.params


class WorkflowCountsByCPerformerQuery(
    SqlQueryObject
):

    def __init__(
        self,
        user_id: int,
        account_id: int,
        status: Optional[str] = None,
        is_external: Optional[bool] = None,
        template_ids: Optional[List[int]] = None,
        template_task_ids: Optional[List[int]] = None,
        workflow_starter_ids: Optional[List[int]] = None
    ):
        self.status = WorkflowStatus.RUNNING
        self.params = {
            'user_id': user_id,
            'account_id': account_id,
            'directly_status': DirectlyStatus.DELETED,
            'status': self.status
        }
        self.is_external = is_external
        # Works for running workflows only
        self.template_ids = template_ids
        self.template_task_ids = template_task_ids
        self.workflow_starter_ids = workflow_starter_ids

    def _get_template_ids(self):
        result, params = self._to_sql_list(
            values=self.template_ids,
            prefix='template_id'
        )
        self.params.update(params)
        return f"pw.template_id in {result}"

    def _get_template_task_ids(self):
        result, params = self._to_sql_list(
            values=self.template_task_ids,
            prefix='template_task_id'
        )
        self.params.update(params)
        return f"pt.template_id in {result}"

    def _get_workflow_starter_ids(self):
        result, params = self._to_sql_list(
            values=self.workflow_starter_ids,
            prefix='workflow_starter_id'
        )
        self.params.update(params)
        return f"pw.workflow_starter_id in {result}"

    def _get_is_external(self):
        self.params.update({'is_external': self.is_external})
        return 'pw.is_external = %(is_external)s'

    def _get_inner_where(self):
        where = """
            WHERE au.is_deleted IS FALSE
            AND pw.is_deleted IS FALSE
            AND pw.account_id = %(account_id)s
            AND ptra.user_id = %(user_id)s
            AND ptp.directly_status != %(directly_status)s """

        if self.template_ids:
            where = f'{where} AND {self._get_template_ids()}'

        if self.template_task_ids:
            where = (
                f'{where} AND {self._get_template_task_ids()}'
                f'AND pt.is_deleted IS FALSE'
            )
        if self.workflow_starter_ids and self.is_external:
            where = (
                f'{where} AND ('
                f'{self._get_workflow_starter_ids()} '
                f'OR {self._get_is_external()})'
            )
        elif self.workflow_starter_ids:
            where = f'{where} AND {self._get_workflow_starter_ids()}'

        elif self.is_external is not None:
            where = f'{where} AND {self._get_is_external()}'

        if self.status is not None:
            where = f'{where} AND pw.status = %(status)s'

        return where

    def _get_from(self):
        result = """
        FROM processes_workflow pw
            LEFT JOIN processes_template t ON t.id = pw.template_id
            LEFT JOIN processes_template_template_owners ptra
              ON t.id = ptra.template_id
            LEFT JOIN accounts_user au ON au.id = ptra.user_id
            INNER JOIN processes_task pt
              ON (pw.id = pt.workflow_id AND pw.current_task = pt.number)
            INNER JOIN processes_taskperformer ptp
              ON pt.id = ptp.task_id
        """
        return result

    def _get_inner_sql(self):
        return f"""
        SELECT
          ptp.user_id AS user_id,
          COUNT(pw.id) AS workflows_count
        {self._get_from()}
        {self._get_inner_where()}
        GROUP BY ptp.user_id
        ORDER BY ptp.user_id ASC """

    def get_sql(self):
        sql = self._get_inner_sql()
        return sql, self.params


class WorkflowCountsByTemplateTaskQuery(
    SqlQueryObject
):

    def __init__(
        self,
        user_id: int,
        account_id: int,
        status: Optional[str] = None,
        is_external: Optional[bool] = None,
        template_ids: Optional[List[int]] = None,
        workflow_starter_ids: Optional[List[int]] = None,
        current_performer_ids: Optional[List[int]] = None,
    ):
        self.status = WorkflowApiStatus.MAP[status] if status else None
        self.params = {
            'user_id': user_id,
            'account_id': account_id,
            'directly_status': DirectlyStatus.DELETED,
            'status': self.status
        }
        self.is_external = is_external
        self.template_ids = template_ids
        self.workflow_starter_ids = workflow_starter_ids
        self.current_performer_ids = current_performer_ids

    def _get_template_ids(self):
        result, params = self._to_sql_list(
            values=self.template_ids,
            prefix='template_id'
        )
        self.params.update(params)
        return f"pw.template_id in {result}"

    def _get_current_performer_ids(self):
        result, params = self._to_sql_list(
            values=self.current_performer_ids,
            prefix='current_performer_id'
        )
        self.params.update(params)
        return f"ptp.user_id in {result}"

    def _get_workflow_starter_ids(self):
        result, params = self._to_sql_list(
            values=self.workflow_starter_ids,
            prefix='workflow_starter_id'
        )
        self.params.update(params)
        return f"pw.workflow_starter_id in {result}"

    def _get_is_external(self):
        self.params.update({'is_external': self.is_external})
        return 'pw.is_external = %(is_external)s'

    def _get_cte_where(self):
        result, params = self._to_sql_list(
            values=TemplateType.TYPES_ONBOARDING,
            prefix='template_type'
        )
        self.params.update(params)
        where = f"""
          WHERE au.is_deleted IS FALSE
            AND t.account_id = %(account_id)s
            AND ptra.user_id = %(user_id)s
            AND t.type NOT IN {result}"""

        if self.template_ids:
            result, params = self._to_sql_list(
                values=self.template_ids,
                prefix='template_id'
            )
            self.params.update(params)
            where += f' AND t.id in {result}'
        return where

    def _get_inner_where(self):
        where = """
            WHERE pw.is_deleted IS FALSE
            AND pw.account_id = %(account_id)s
            AND ptp.directly_status != %(directly_status)s """

        if self.template_ids:
            where = f'{where} AND {self._get_template_ids()}'

        if self.workflow_starter_ids and self.is_external:
            where = (
                f'{where} AND ('
                f'{self._get_workflow_starter_ids()} '
                f'OR {self._get_is_external()})'
            )
        elif self.workflow_starter_ids:
            where = f'{where} AND {self._get_workflow_starter_ids()}'

        elif self.is_external is not None:
            where = f'{where} AND {self._get_is_external()}'

        if self.current_performer_ids:
            where = (
                f'{where} AND {self._get_current_performer_ids()} '
                f'AND ptp.directly_status != %(directly_status)s '
                f'AND pt.is_deleted IS FALSE '
            )

        if self.status is not None:
            where = f'{where} AND pw.status = %(status)s'

        return where

    def _get_from(self):
        result = """
        FROM processes_workflow pw
            INNER JOIN processes_task pt
              ON pw.id = pt.workflow_id
              AND pw.current_task = pt.number
            INNER JOIN processes_taskperformer ptp
              ON pt.id = ptp.task_id
        """
        return result

    def _get_inner_sql(self):
        return f"""
        WITH
          template_tasks AS (
            SELECT
              tt.id,
              tt.number
            FROM processes_template t
              INNER JOIN processes_tasktemplate tt
                ON t.id = tt.template_id
                AND t.is_deleted IS FALSE
                AND tt.is_deleted IS FALSE
              INNER JOIN processes_template_template_owners ptra
                ON t.id = ptra.template_id
              INNER JOIN accounts_user au ON au.id = ptra.user_id
            {self._get_cte_where()}
          ),
          result AS (
            SELECT
              template_task_id,
              COUNT(workflow_id) AS workflows_count
            FROM (
              SELECT
                pt.template_id AS template_task_id,
                pw.id AS workflow_id
              {self._get_from()}
              {self._get_inner_where()}
              GROUP BY
                pw.id,
                pt.template_id
            ) wf_by_template_tasks
            GROUP BY template_task_id
          )

        SELECT
          tt.id AS template_task_id,
          COALESCE(result.workflows_count, 0) AS workflows_count
        FROM template_tasks tt
          LEFT JOIN result ON tt.id = result.template_task_id
        ORDER BY tt.id ASC """

    def get_sql(self):
        sql = self._get_inner_sql()
        return sql, self.params


class TaskListQuery(
    SqlQueryObject,
    SearchSqlQueryMixin,
    OrderByMixin,
):
    ordering_map = TaskOrdering.MAP

    def __init__(
        self,
        user: UserModel,
        template_id: Optional[int] = None,
        template_task_id: Optional[int] = None,
        ordering: Optional[TaskOrdering] = None,
        assigned_to: Optional[int] = None,
        search: Optional[str] = None,
        is_completed: bool = False,
        **kwargs
    ):

        """ Search string should be validated """

        self.template_id = template_id
        self.template_task_id = template_task_id
        self.ordering = ordering
        self.is_completed = bool(is_completed)
        self.assigned_to = user.id if assigned_to is None else assigned_to
        self.search_text = search
        self.params = {
            'account_id': user.account_id,
            'directly_status': DirectlyStatus.DELETED,
            'assigned_to': self.assigned_to,
            'wf_status': WorkflowStatus.RUNNING,
        }

    def _get_search(self):
        tsquery, params = self._get_tsquery()
        self.params.update(params)
        return f"""
            (
            {self._search_in(table='pt', tsquery=tsquery)}
            OR
            {self._search_in(table='pw', tsquery=tsquery)}
            OR
            {self._search_in(table='au', tsquery=tsquery)}
            OR
            {self._search_in(table='we', tsquery=tsquery)}
            OR
            {self._search_in(table='t', tsquery=tsquery)}
            OR
            {self._search_in(table='fa', tsquery=tsquery)}
            OR
            {self._search_in(table='ptf', tsquery=tsquery)}
            OR
            {self._search_in(table='kv', tsquery=tsquery)}
            )
        """

    def get_is_completed_where(self):
        if self.is_completed:
            return 'ptp.is_completed IS TRUE'
        else:
            return """
                pw.current_task = pt.number
                AND ptp.is_completed IS FALSE
                AND pw.status = %(wf_status)s
            """

    def _get_template_task_id(self):
        self.params['template_task_id'] = self.template_task_id
        return 'pt.template_id = %(template_task_id)s'

    def _get_template_id(self):
        self.params['template_id'] = self.template_id
        return 't.id = %(template_id)s'

    def _get_inner_where(self):
        where = f"""
            WHERE pt.is_deleted IS FALSE
            AND pw.account_id = %(account_id)s
            AND ptp.user_id = %(assigned_to)s
            AND ptp.directly_status != %(directly_status)s
            AND {self.get_is_completed_where()}
        """

        if self.search_text:
            where += f' AND {self._get_search()}'

        if self.template_task_id:
            where += f' AND {self._get_template_task_id()}'
        if self.template_id:
            where += f' AND {self._get_template_id()}'
        return where

    def _get_tables(self):
        result = """
            FROM processes_task pt
            INNER JOIN processes_workflow pw ON (
              pw.id = pt.workflow_id AND
              pt.is_deleted IS FALSE
            )
            LEFT JOIN processes_taskperformer ptp ON (
              pt.id = ptp.task_id
            )
        """
        if self.search_text:
            result += """
                LEFT JOIN processes_kickoffvalue kv ON pw.id = kv.workflow_id
                LEFT JOIN processes_workflowevent we ON (
                  we.is_deleted IS FALSE AND
                  we.status != 'deleted' AND
                  we.type = 5 AND
                  pt.id = we.task_id
                )
                LEFT JOIN accounts_user au ON (
                  au.id = ptp.user_id AND
                  au.is_deleted IS FALSE
                )
                LEFT JOIN processes_fileattachment fa ON (
                  pw.id=fa.workflow_id AND
                  fa.is_deleted is FALSE
                )
                LEFT JOIN processes_taskfield ptf ON (
                    (
                       ptf.task_id = pt.id
                       OR ptf.kickoff_id = kv.id
                    ) AND
                    ptf.is_deleted IS FALSE
                )
            """
        if self.search_text or self.template_id:
            result += """
                LEFT JOIN processes_template t ON (
                  t.id = pw.template_id AND
                  t.is_deleted IS FALSE
                )
            """
        return result

    def _get_inner_sql(self):
        return f"""
            SELECT DISTINCT ON (pt.id) pt.id,
                pt.name,
                pw.name as workflow_name,
                pt.due_date,
                EXTRACT(
                  EPOCH FROM pt.due_date AT TIME ZONE 'UTC'
                ) AS due_date_tsp,
                pt.date_started,
                EXTRACT(
                  EPOCH FROM pt.date_started AT TIME ZONE 'UTC'
                ) AS date_started_tsp,
                ptp.date_completed,
                EXTRACT(
                  EPOCH FROM pt.date_completed AT TIME ZONE 'UTC'
                ) AS date_completed_tsp,
                pw.template_id as template_id,
                pt.template_id as template_task_id,
                pt.is_urgent
            {self._get_tables()}
            {self._get_inner_where()}
            ORDER BY pt.id
        """

    def get_sql(self):
        order_by = self.get_order_by(
            pre_columns=None if self.is_completed else 'tasks.is_urgent DESC',
            default_column='tasks.date_started DESC',
        )
        s = f"""
            SELECT *
            FROM ({self._get_inner_sql()}) AS tasks
            {order_by}
        """
        return s, self.params


class TemplateListQuery(
    SqlQueryObject,
    SearchSqlQueryMixin,
    OrderByMixin,
):
    ordering_map = TemplateOrdering.MAP

    def __init__(
        self,
        user: User,
        account_id: str,
        ordering: Optional[str] = None,
        search_text: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_public: Optional[bool] = None,
        is_template_owner: Optional[bool] = None,
    ):

        self.user = user
        self.account_id = account_id
        self.params = {
            'account_id': self.account_id,
            'user_id': user.id,
        }
        self.order = None
        self.is_active = is_active
        self.is_public = is_public
        self.is_template_owner = is_template_owner
        self.ordering = ordering
        self.search_text = search_text

    def _get_search(self):
        tsquery, params = self._get_tsquery()
        self.params.update(params)
        return f"""
            (
              {self._search_in(table='pt', tsquery=tsquery)}
              OR {self._search_in(table='ptt', tsquery=tsquery)}
              OR {self._search_in(table='accounts_user', tsquery=tsquery)}
            )
        """

    def _get_allowed(self):
        self.params.update({'allowed_id': self.user.id})
        return """ptra.user_id = %(allowed_id)s"""

    def _get_active(self):
        self.params.update({'is_active': self.is_active})
        return 'pt.is_active IS %(is_active)s'

    def _get_public(self):
        self.params.update({'is_public': self.is_public})
        return 'pt.is_public IS %(is_public)s'

    def _get_filter_by_type(self):
        result, params = self._to_sql_list(
            values=TemplateType.TYPES_ONBOARDING,
            prefix='template_type'
        )
        self.params.update(params)
        return f"pt.type NOT IN {result}"

    def get_workflows_join(self):
        if self.ordering in {
            TemplateOrdering.USAGE,
            TemplateOrdering.REVERSE_USAGE
        }:
            return """
                LEFT JOIN processes_workflow workflows ON (
                  pt.id = workflows.template_id AND
                  workflows.is_deleted = FALSE
                )
            """
        return ''

    def get_workflows_select(self):
        if self.ordering in {
            TemplateOrdering.USAGE,
            TemplateOrdering.REVERSE_USAGE
        }:
            return 'COUNT(DISTINCT workflows.id) AS workflows_count,'
        return ''

    def _get_inner_where(self):
        where = """
        WHERE pt.is_deleted = false AND
        pt.account_id = %(account_id)s AND
        accounts_user.id = %(user_id)s
        """

        where = f'{where} AND {self._get_filter_by_type()}'

        if self.search_text:
            where = f'{where} AND {self._get_search()}'

        if self.is_active is not None:
            where = f'{where} AND {self._get_active()}'

        if (
            not self.user.is_account_owner
            and self.is_template_owner is not None
        ):
            where = f'{where} AND {self._get_allowed()}'

        if self.is_public is not None:
            where = f'{where} AND {self._get_public()}'

        return where

    def _get_inner_sql(self):
        return f"""
        SELECT DISTINCT
            pt.id,
            pt.is_deleted,
            pt.name,
            pt.wf_name_template,
            pt.description,
            pt.date_created,
            pt.finalizable,
            pt.account_id,
            pt.is_active,
            pt.is_public,
            pt.is_embedded,
            pt.type,
            pt.search_content,
            pt.performers_count,
            {self.get_workflows_select()}
            pt.tasks_count
        FROM processes_template pt
        LEFT JOIN processes_tasktemplate ptt ON (
          ptt.template_id = pt.id AND
          ptt.is_deleted = false
        )
        LEFT JOIN processes_template_template_owners ptra ON (
          pt.id = ptra.template_id
        )
        LEFT JOIN accounts_user ON (
          ptra.user_id = accounts_user.id AND
          accounts_user.is_deleted = false
        )
        {self.get_workflows_join()}

        {self._get_inner_where()}
        GROUP BY pt.id
        """

    def get_sql(self):
        order_by = self.get_order_by(
            pre_columns='templates.is_active DESC',
            default_column='templates.id'
        )
        return f"""
        SELECT *
        FROM ({self._get_inner_sql()}) templates
        {order_by}
        """, self.params


class RunningTaskTemplateQuery(SqlQueryObject):
    def __init__(self, template_id: int, user_id: int):
        self._template_id = template_id
        self._user_id = user_id

    def get_sql(self):
        return """
          SELECT DISTINCT
            ptt.id,
            ptt.name,
            ptt.number
          FROM processes_tasktemplate ptt
          JOIN processes_task pt ON ptt.id = pt.template_id
          JOIN processes_workflow wf ON pt.workflow_id = wf.id AND
            wf.status = %(running_status)s
          JOIN processes_taskperformer ptp on pt.id = ptp.task_id AND
            ptp.user_id = %(user_id)s AND
            ptp.is_completed IS FALSE AND
            ptp.directly_status != %(directly_status)s
          WHERE ptt.is_deleted IS FALSE AND
            ptt.template_id = %(template_id)s AND
            pt.is_deleted IS FALSE AND
            pt.date_started IS NOT NULL AND
            pt.is_completed IS FALSE
          ORDER BY ptt.number;
        """, {
            'user_id': self._user_id,
            'template_id': self._template_id,
            'running_status': WorkflowStatus.RUNNING,
            'directly_status': DirectlyStatus.DELETED
        }


class TemplateStepsQuery(
    SqlQueryObject,
):

    def __init__(
        self,
        user: User,
        template_id: int,
        with_tasks_in_progress: Optional[bool] = None,
        is_running_workflows: Optional[bool] = None
    ):

        if (
            is_running_workflows is not None
            and with_tasks_in_progress is not None
        ):
            raise Exception(MSG_PW_0022)
        self.with_tasks_in_progress = with_tasks_in_progress
        self.is_running_workflows = is_running_workflows
        if is_running_workflows is True or with_tasks_in_progress is True:
            self.status = WorkflowStatus.RUNNING
        else:
            self.status = None
        self.params = {
            'status': self.status,
            'account_id': user.account.id,
            'user_id': user.id,
            'template_id': template_id,
            'directly_status': DirectlyStatus.DELETED
        }

    def _get_join(self):
        join = ''
        if (
            self.with_tasks_in_progress is not None
            or self.is_running_workflows is not None
        ):
            join += """
                JOIN processes_task pt
                  ON ptt.id = pt.template_id
                JOIN processes_workflow pw
                  ON pt.workflow_id = pw.id """

        if self.with_tasks_in_progress is not None:
            join += """
                JOIN processes_taskperformer ptp
                  ON pt.id = ptp.task_id """
        else:
            join += """
                JOIN processes_template_template_owners ptra
                  ON ptra.template_id = t.id
                    AND ptra.user_id = %(user_id)s """
        return join

    def _get_filter_by_type(self):
        result, params = self._to_sql_list(
            values=TemplateType.TYPES_ONBOARDING,
            prefix='template_type'
        )
        self.params.update(params)
        return f"t.type NOT IN {result}"

    def _get_where(self):
        where = ""
        if self.is_running_workflows is True:
            where += f"""
                AND pt.is_deleted IS FALSE
                AND pt.date_started IS NOT NULL
                AND pt.is_completed IS FALSE
                AND ptt.number = pw.current_task """
            if self.status is not None:
                where = f'{where} AND pw.status = %(status)s'
        elif self.with_tasks_in_progress is not None:
            completed_flag = "FALSE" if self.with_tasks_in_progress else "TRUE"
            where += f"""
                AND pt.is_deleted IS FALSE
                AND pt.date_started IS NOT NULL
                AND ptp.user_id = %(user_id)s
                AND ptp.directly_status != %(directly_status)s
                AND ptp.is_completed IS {completed_flag} """
            if self.with_tasks_in_progress is True:
                where += f"""AND ptt.number = pw.current_task """
                if self.status is not None:
                    where = f'{where} AND pw.status = %(status)s'
        return where

    def get_sql(self):
        return f"""
            SELECT DISTINCT
              ptt.id,
              ptt.name,
              ptt.number
            FROM processes_template t
              JOIN processes_tasktemplate ptt
                ON ptt.template_id = t.id
              {self._get_join()}
            WHERE
              ptt.is_deleted IS FALSE
              AND t.is_deleted IS FALSE
              AND t.id = %(template_id)s
              AND t.account_id = %(account_id)s
              AND {self._get_filter_by_type()}
              {self._get_where()}
            ORDER BY ptt.number;
        """, self.params


class WorkflowCurrentTaskUserPerformerQuery(SqlQueryObject):

    def __init__(
        self,
        user: User,
        workflow_id: int,
        task_id: Optional[int] = None
    ):
        self.params = {
            'account_id': user.account.id,
            'user_id': user.id,
            'workflow_id': workflow_id,
            'directly_status': DirectlyStatus.DELETED,
            'task_id': task_id
        }

    def _get_workflow_current_task_performer_query(self):
        return f"""
            SELECT ptp.id
            FROM processes_workflow pw
              INNER JOIN processes_task pt
                ON pt.workflow_id=pw.id
                  AND pt.number = pw.current_task
              INNER JOIN processes_taskperformer ptp
                ON ptp.task_id = pt.id
            WHERE ptp.user_id = %(user_id)s
              AND ptp.directly_status != %(directly_status)s
              AND pw.id = %(workflow_id)s
              AND pt.account_id = %(account_id)s
        """

    def _get_workflow_task_performer_query(self):
        return f"""
            SELECT ptp.id
            FROM processes_task pt
              INNER JOIN processes_taskperformer ptp
                ON ptp.task_id = pt.id
            WHERE ptp.user_id = %(user_id)s
              AND ptp.directly_status != %(directly_status)s
              AND pt.workflow_id = %(workflow_id)s
              AND pt.account_id = %(account_id)s
              AND pt.id = %(task_id)s
        """

    def get_sql(self):
        if self.params['task_id']:
            query = self._get_workflow_task_performer_query()
        else:
            query = self._get_workflow_current_task_performer_query()
        return query, self.params


class TaskWorkflowMemberQuery(SqlQueryObject):

    def __init__(
        self,
        user: User,
        task_id: Optional[int] = None
    ):
        self.params = {
            'account_id': user.account.id,
            'user_id': user.id,
            'task_id': task_id
        }

    def get_sql(self):
        query = """
            SELECT pw.id
            FROM processes_task pt
              INNER JOIN processes_workflow pw
                ON pw.id = pt.workflow_id
              INNER JOIN processes_workflow_members pwm
                ON pwm.workflow_id = pw.id
                AND pwm.user_id = %(user_id)s
            WHERE
              pt.id = %(task_id)s
              AND pt.is_deleted IS FALSE
              AND pt.account_id = %(account_id)s
            LIMIT 1
        """

        return query, self.params


class HighlightsQuery(SqlQueryObject):

    event_types = (
        WorkflowEventType.COMMENT,
        WorkflowEventType.TASK_COMPLETE,
        WorkflowEventType.RUN,
        WorkflowEventType.COMPLETE,
        WorkflowEventType.ENDED,
        WorkflowEventType.TASK_REVERT,
        WorkflowEventType.REVERT,
        WorkflowEventType.URGENT,
        WorkflowEventType.NOT_URGENT,
        WorkflowEventType.TASK_PERFORMER_CREATED,
        WorkflowEventType.TASK_PERFORMER_DELETED,
        WorkflowEventType.FORCE_DELAY,
        WorkflowEventType.FORCE_RESUME,
        WorkflowEventType.DUE_DATE_CHANGED,
        WorkflowEventType.SUB_WORKFLOW_RUN,
    )

    def __init__(
        self,
        account_id,
        user_id,
        templates=None,
        users=None,
        date_before: Optional[datetime] = None,
        date_after: Optional[datetime] = None,
    ):

        # TODO Refactoring need

        from rest_framework.exceptions import ValidationError

        self.sql_params = {'account_id': account_id, 'user_id': user_id}

        if templates is not None:
            try:
                self.templates = literal_eval(templates)
            except (SyntaxError, ValueError):
                raise ValidationError(MSG_PW_0024('templates'))

        if users is not None:
            try:
                self.users = literal_eval(users)
                if isinstance(self.users, int):
                    self.users = (self.users,)
            except (SyntaxError, ValueError):
                raise ValidationError(MSG_PW_0024('users'))

        if date_before is not None:
            self.date_before = date_before

        if date_after is not None:
            self.date_after = date_after

    def get_sql(self):
        subquery = f"""
        SELECT DISTINCT ON (we.workflow_id)
          we.id,
          we.type,
          we.task_json,
          we.delay_json,
          we.text,
          we.created,
          we.user_id,
          we.target_user_id,
          we.workflow_id
        FROM processes_workflowevent we
        LEFT JOIN processes_workflow workflow ON
          we.workflow_id = workflow.id
        LEFT JOIN processes_template template ON
          workflow.template_id = template.id
        LEFT JOIN processes_template_template_owners template_owners ON
          template.id = template_owners.template_id
        WHERE
          NOT we.is_deleted AND
          we.account_id = %(account_id)s AND
          NOT workflow.is_deleted AND
          NOT template.is_deleted AND
          template_owners.user_id = %(user_id)s
        """
        ordering = 'ORDER BY we.created DESC, we.id DESC'
        sub_ordering = ' ORDER BY we.workflow_id, we.created DESC'
        additional_where = []
        where = []

        result, params = self._to_sql_list(self.event_types, 'type')
        self.sql_params.update(params)
        additional_where.append(
            f'we.type in {result}'
        )

        if hasattr(self, 'users'):
            result, params = self._to_sql_list(self.users, 'user')
            self.sql_params.update(params)
            additional_where.append(
                f'we.user_id in {result}'
            )

        if hasattr(self, 'templates'):
            result, params = self._to_sql_list(self.templates, 'template')
            self.sql_params.update(params)
            additional_where.append(
                f'workflow.template_id in {result}'
            )

        if hasattr(self, 'date_before'):
            self.sql_params['date_before'] = self.date_before
            where.append(f'we.created <= %(date_before)s')

        if hasattr(self, 'date_after'):
            self.sql_params['date_after'] = self.date_after
            where.append(f'we.created >= %(date_after)s')

        if additional_where:
            additional_where = ' AND '.join(additional_where)
            subquery += f'AND {additional_where}'

        if where:
            where = ' AND '.join(where)
            where = f'WHERE {where}'
        else:
            where = ''

        subquery += sub_ordering

        return f"""
          SELECT
            we.*
          FROM ({subquery}
          ) AS we
          {where}
          {ordering}
        """, self.sql_params


class UpdateWorkflowEventWatchedQuery(SqlQueryObject):
    """ Construct ARRAY[]::jsonb[] from newly created
        WorkflowEventAction records and add to WorkflowEvent.watched array """

    def __init__(
        self,
        actions_ids: List[int]
    ):
        self.actions_ids = actions_ids
        self.params = {}

    def get_actions_ids(self) -> str:
        result, params = self._to_sql_list(self.actions_ids, 'actions_ids')
        self.params.update(params)
        return result

    def get_sql(self) -> Tuple[str, dict]:
        query = f"""
        UPDATE processes_workflowevent
        SET watched = updated.watched
        FROM (
          SELECT
            we.id,
            (
              array_agg(wea.new_watched)::jsonb[]
              || COALESCE(we.watched, ARRAY[]::jsonb[])
            ) AS watched
          FROM (
              SELECT
                event_id,
                json_build_object(
                  'date_tsp', EXTRACT(EPOCH FROM (created AT TIME ZONE 'UTC')),
                  'date', created,
                  'user_id', user_id) AS new_watched
              FROM processes_workfloweventaction
              WHERE id IN {self.get_actions_ids()}
            ) AS wea
            JOIN processes_workflowevent we ON we.id = wea.event_id
          GROUP BY we.id
        ) AS updated
        WHERE processes_workflowevent.id = updated.id
        RETURNING processes_workflowevent.id
        """
        return query, self.params


class TemplateTitlesEventsQuery(SqlQueryObject):
    event_types = [
        WorkflowEventType.COMMENT,
        WorkflowEventType.TASK_COMPLETE,
        WorkflowEventType.RUN,
        WorkflowEventType.COMPLETE,
        WorkflowEventType.ENDED,
        WorkflowEventType.TASK_REVERT,
        WorkflowEventType.REVERT,
        WorkflowEventType.URGENT,
        WorkflowEventType.NOT_URGENT,
        WorkflowEventType.TASK_PERFORMER_CREATED,
        WorkflowEventType.TASK_PERFORMER_DELETED,
        WorkflowEventType.FORCE_DELAY,
        WorkflowEventType.FORCE_RESUME,
        WorkflowEventType.DUE_DATE_CHANGED,
        WorkflowEventType.SUB_WORKFLOW_RUN,
    ]

    template_types = (
        TemplateType.ONBOARDING_ACCOUNT_OWNER,
        TemplateType.ONBOARDING_NON_ADMIN,
        TemplateType.ONBOARDING_ADMIN,
    )

    def __init__(
        self,
        user: UserModel,
        event_date_from: Optional[datetime] = None,
        event_date_to: Optional[datetime] = None,
    ):

        self.date_before = event_date_from
        self.date_after = event_date_to
        self.params = {
            'account_id': user.account.id,
            'user_id': user.id,
        }

    def _get_date_condition(self):
        condition = ""
        if self.date_before is not None:
            condition += f""" AND we.created >= '{self.date_before}'"""
        if self.date_after is not None:
            condition += f""" AND we.created < '{self.date_after}'"""
        return condition

    def get_sql(self):
        event_types, event_params = self._to_sql_list(
            values=self.event_types,
            prefix='event_type'
        )
        self.params.update(event_params)
        template_types, template_params = self._to_sql_list(
            values=self.template_types,
            prefix='template_type'
        )
        self.params.update(template_params)

        sql = f"""
        SELECT
          t.id,
          t.name,
          COUNT(DISTINCT pw.id) FILTER (WHERE pw.status = 0) AS workflows_count
        FROM processes_template AS t
          INNER JOIN processes_workflow AS pw ON (
            t.id = pw.template_id AND pw.is_deleted = False
          )
          INNER JOIN processes_workflowevent AS we ON (
            pw.id = we.workflow_id
            AND we.type IN {event_types}
            {self._get_date_condition()}
            AND we.user_id = %(user_id)s
            AND we.is_deleted = False
          )
        WHERE t.is_deleted = False
          AND t.account_id = %(account_id)s
          AND NOT (t.type IN {template_types})
        GROUP BY t.id, t.name
        ORDER BY workflows_count DESC, t.name ASC """
        return sql, self.params


class TemplateTitlesQuery(SqlQueryObject):

    template_types = (
        TemplateType.ONBOARDING_ACCOUNT_OWNER,
        TemplateType.ONBOARDING_NON_ADMIN,
        TemplateType.ONBOARDING_ADMIN,
    )

    def __init__(
        self,
        user: User,
        with_tasks_in_progress: Optional[bool] = None,
        workflows_status: Optional[WorkflowStatus] = None,
    ):
        self.with_tasks_in_progress = with_tasks_in_progress
        self.status = workflows_status
        self.params = {
            'account_id': user.account.id,
            'user_id': user.id,
            'directly_status': DirectlyStatus.DELETED,
        }

    def get_from(self):
        if self.with_tasks_in_progress:
            self.params['status'] = WorkflowStatus.RUNNING
            pw_clause = "AND pw.status = %(status)s"
        elif self.status:
            self.params['status'] = WorkflowApiStatus.MAP[self.status]
            pw_clause = "AND pw.status = %(status)s"
        else:
            pw_clause = ""
        result = f"""
        FROM processes_template AS t
          INNER JOIN processes_workflow pw ON (
            t.id = pw.template_id
            AND pw.is_deleted = False
            {pw_clause}
          ) """
        if self.with_tasks_in_progress is None:
            result += """
            INNER JOIN processes_template_template_owners pto ON (
                t.id = pto.template_id
                AND pto.user_id = %(user_id)s
            )
            """
        else:
            if self.with_tasks_in_progress:
                pt_join_clause = "AND pw.current_task = pt.number"
                ptp_join_clause = "AND ptp.is_completed = FALSE"
            else:
                pt_join_clause = ""
                ptp_join_clause = "AND ptp.is_completed = TRUE"
            result += f"""
                INNER JOIN processes_task pt ON (
                  pw.id = pt.workflow_id
                  AND pt.date_started IS NOT NULL
                  AND pt.is_deleted = False
                  {pt_join_clause}
                )
                INNER JOIN processes_taskperformer ptp ON (
                  pt.id = ptp.task_id
                  AND ptp.is_deleted = False
                  AND ptp.directly_status != %(directly_status)s
                  AND ptp.user_id = %(user_id)s
                  {ptp_join_clause}
                ) """
        return result

    def get_sql(self) -> Tuple[str, dict]:
        template_types, template_params = self._to_sql_list(
            values=self.template_types,
            prefix='template_type'
        )
        self.params.update(template_params)
        from_clause = self.get_from()
        sql = f"""
            SELECT
              t.id,
              t.name,
              COUNT(DISTINCT pw.id) AS workflows_count
            {from_clause}
            WHERE t.is_deleted = False
              AND t.account_id = %(account_id)s
              AND NOT t.type IN {template_types}
            GROUP BY t.id
            ORDER BY workflows_count DESC, t.name ASC """
        return sql, self.params
