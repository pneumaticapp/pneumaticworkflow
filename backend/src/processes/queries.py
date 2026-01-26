# ruff: noqa: PLC0415
from ast import literal_eval
from datetime import datetime
from typing import List, Optional, Tuple

from django.contrib.auth import get_user_model

from src.accounts.models import User, UserGroup
from src.generics.mixins.managers import SearchSqlQueryMixin
from src.generics.mixins.queries import (
    DereferencedOwnersMixin,
    DereferencedPerformersMixin,
)
from src.processes.enums import (
    DirectlyStatus,
    TaskOrdering,
    TaskStatus,
    TemplateOrdering,
    TemplateType,
    WorkflowApiStatus,
    WorkflowEventType,
    WorkflowOrdering,
    WorkflowStatus,
)
from src.processes.messages.workflow import (
    MSG_PW_0024,
)
from src.processes.paginations import WorkflowListPagination
from src.queries import (
    OrderByMixin,
    SqlQueryObject,
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
        limit: Optional[int] = WorkflowListPagination.default_limit,
        user_id:  Optional[int] = None,
        offset: Optional[int] = None,
        status: Optional[str] = None,
        ordering: Optional[WorkflowOrdering.LITERALS] = None,
        template: Optional[List[int]] = None,
        task_api_name: Optional[List[str]] = None,
        current_performer: Optional[List[int]] = None,
        current_performer_group_ids: Optional[List[int]] = None,
        workflow_starter: Optional[List[int]] = None,
        is_external: Optional[bool] = None,
        search: Optional[str] = None,
        ancestor_task_id: Optional[int] = None,
    ):
        self.params = {
            'account_id': account_id,
            'limit': limit,
        }
        self.status = WorkflowApiStatus.MAP[status] if status else None
        if self.status == WorkflowStatus.RUNNING:
            self.tasks_status = (TaskStatus.ACTIVE,)
        elif self.status == WorkflowStatus.DELAYED:
            self.tasks_status = (TaskStatus.DELAYED,)
        elif self.status == WorkflowStatus.DONE:
            self.tasks_status = (TaskStatus.COMPLETED,)
        else:
            self.tasks_status = (
                TaskStatus.ACTIVE,
                TaskStatus.DELAYED,
                TaskStatus.COMPLETED,
            )
        self.offset = offset
        self.ordering = ordering
        self.template = template
        self.task_api_name = task_api_name
        self.current_performer = current_performer
        self.current_performer_group_ids = current_performer_group_ids
        self.workflow_starter = workflow_starter
        self.is_external = is_external
        self.search_text = search
        self.ancestor_task_id = ancestor_task_id
        self.user_id = user_id

    def _get_search(self):
        tsquery, params = self._get_tsquery()
        self.params.update(params)
        return f"""
            {self._search_in(table='ps', field='content', tsquery=tsquery)}
        """

    def _get_template(self):
        result, params = self._to_sql_list(
            values=self.template,
            prefix='template',
        )
        self.params.update(params)
        return f"pw.template_id in {result}"

    def _get_template_task(self):
        result, params = self._to_sql_list(
            values=self.task_api_name,
            prefix='task_api_name',
        )
        self.params.update(params)
        return f"""
            pt.api_name IN {result}
            AND pt.status IN ('{"','".join(self.tasks_status)}')
        """

    def _get_current_performer(self):
        result, params = self._to_sql_list(
            values=self.current_performer,
            prefix='current_performer',
        )
        self.params.update(params)
        return f"ptp.user_id in {result}"

    def _get_current_performer_group_ids(self):
        result, params = self._to_sql_list(
            values=self.current_performer_group_ids,
            prefix='current_performer_group_ids',
        )
        self.params.update(params)
        return f"ptp.group_id in {result}"

    def _get_workflow_starter(self):
        result, params = self._to_sql_list(
            values=self.workflow_starter,
            prefix='workflow_starter',
        )
        self.params.update(params)
        return f"pw.workflow_starter_id in {result}"

    def _get_is_external(self):
        self.params.update({'is_external': self.is_external})
        return "pw.is_external = %(is_external)s"

    def _get_offset(self):
        if self.offset:
            self.params['offset'] = self.offset
            return "OFFSET %(offset)s"
        return ""

    def _get_where(self):
        where = """
            WHERE pw.is_deleted IS FALSE
            AND pw.account_id = %(account_id)s """

        if self.user_id:
            where = f"""{where}
                AND (
                    pwo.user_id = %(user_id)s
                    OR pw.workflow_starter_id = %(user_id)s
                )"""
            self.params['user_id'] = self.user_id

        if self.template:
            where = f'{where} AND {self._get_template()}'

        if self.task_api_name:
            where = f'{where} AND {self._get_template_task()}'

        if self.current_performer and self.current_performer_group_ids:
            where = f"""
                {where}
                AND (
                    {self._get_current_performer()}
                    OR {self._get_current_performer_group_ids()}
                )
                AND ptp.directly_status != '{DirectlyStatus.DELETED}'
            """
        elif self.current_performer:
            where = f"""
                {where}
                 AND {self._get_current_performer()}
                 AND ptp.directly_status != '{DirectlyStatus.DELETED}'
            """
        elif self.current_performer_group_ids:
            where = f"""
                {where}
                AND {self._get_current_performer_group_ids()}
                AND ptp.directly_status != '{DirectlyStatus.DELETED}'
            """

        if self.workflow_starter and self.is_external:
            where = f"""
                {where}
                AND (
                    {self._get_workflow_starter()}
                    OR {self._get_is_external()}
                )"""
        elif self.workflow_starter:
            where = f'{where} AND {self._get_workflow_starter()}'

        elif self.is_external is not None:
            where = f'{where} AND {self._get_is_external()}'

        if self.search_text:
            where = f'{where} AND {self._get_search()}'

        if self.status is not None:
            where = f'{where} AND pw.status = %(status)s'
            self.params['status'] = self.status

        if self.ancestor_task_id:
            where = f'{where} AND pw.ancestor_task_id = %(ancestor_task_id)s'
            self.params['ancestor_task_id'] = self.ancestor_task_id

        return where

    def _get_from(self):
        result = """
            FROM processes_workflow pw
            LEFT JOIN processes_workflow_owners pwo ON (
                pw.id = pwo.workflow_id
            )
            INNER JOIN processes_task pt ON (
                pw.id = pt.workflow_id
                AND pt.is_deleted IS FALSE
            )
        """

        if self.current_performer or self.current_performer_group_ids:
            result += f"""
                LEFT JOIN processes_taskperformer ptp ON (
                    pt.id = ptp.task_id
                    AND pt.status IN ('{"','".join(self.tasks_status)}')
                )
            """

        if self.search_text:
            result += """
                LEFT JOIN processes_searchcontent ps (
                    pw.id = ps.workflow_id AND
                    ps.is_deleted IS FALSE
                )
            """
        return result

    def _get_select(self):
        return f"""
        SELECT
            pw.id,
            pw.name,
            pw.template_id,
            pw.status,
            pw.description,
            pw.is_legacy_template,
            pw.legacy_template_name,
            pw.is_external,
            pw.is_urgent,
            pw.date_created,
            pw.date_completed,
            pw.due_date,
            pw.workflow_starter_id,
            pw.ancestor_task_id,
            pw.finalizable,
            MIN(pt.due_date) FILTER(
                WHERE pt.status = '{TaskStatus.ACTIVE}'
            ) AS nearest_due_date
        """

    def get_sql(self) -> str:
        post_columns = None
        default_column = 'workflows.date_created DESC'
        if self.ordering == WorkflowOrdering.URGENT_FIRST:
            post_columns = default_column
        order_by = self.get_order_by(
            default_column=default_column,
            post_columns=post_columns,
        )
        return f"""
            SELECT *
            FROM (
                {self._get_select()}
                {self._get_from()}
                {self._get_where()}
                GROUP BY pw.id
                ORDER BY pw.id
            ) AS workflows
            {order_by}
            LIMIT %(limit)s {self._get_offset()}
        """

    def get_count_sql(self) -> str:
        return f"""
        SELECT
            1 AS id,
            COUNT(id) AS count
        FROM (
            SELECT pw.id
            {self._get_from()}
            {self._get_where()}
            GROUP BY pw.id
        ) AS count_workflows
        """


class WorkflowCountsByWfStarterQuery(
    SqlQueryObject,
):

    def __init__(
        self,
        user_id: int,
        account_id: int,
        status: Optional[str] = None,
        template_ids: Optional[List[int]] = None,
        current_performer_ids: Optional[List[int]] = None,
        current_performer_group_ids: Optional[List[int]] = None,
    ):
        self.status = WorkflowApiStatus.MAP[status] if status else None
        self.params = {
            'user_id': user_id,
            'account_id': account_id,
            'status': self.status,
        }
        self.template_ids = template_ids
        self.current_performer_ids = current_performer_ids

        if current_performer_ids:
            group_ids = (
                UserGroup.objects
                .filter(users__in=current_performer_ids)
                .values_list('id', flat=True)
            )
            if current_performer_group_ids:
                current_performer_group_ids = (
                    set(current_performer_group_ids) | set(group_ids)
                )
            else:
                current_performer_group_ids = set(group_ids)
        self.current_performer_group_ids = current_performer_group_ids

    def _get_template_ids(self):
        result, params = self._to_sql_list(
            values=self.template_ids,
            prefix='template_id',
        )
        self.params.update(params)
        return f"pw.template_id IN {result}"

    def _get_current_performer_ids(self):
        result, params = self._to_sql_list(
            values=self.current_performer_ids,
            prefix='current_performer_id',
        )
        self.params.update(params)
        return f"ptp.user_id in {result}"

    def _get_current_performer_group_ids(self):
        result, params = self._to_sql_list(
            values=self.current_performer_group_ids,
            prefix='current_performer_group_ids',
        )
        self.params.update(params)
        return f"ptp.group_id in {result}"

    def _get_inner_where(self):
        where = """
            WHERE au.is_deleted IS FALSE
            AND pw.is_deleted IS FALSE
            AND pw.account_id = %(account_id)s
            AND ptra.user_id = %(user_id)s """

        if self.template_ids:
            where = f'{where} AND {self._get_template_ids()}'

        if self.current_performer_ids and self.current_performer_group_ids:
            where = f"""
                {where}
                AND (
                    {self._get_current_performer_ids()}
                    OR
                    {self._get_current_performer_group_ids()}
                )
                AND ptp.directly_status != '{DirectlyStatus.DELETED}'
                AND pt.is_deleted IS FALSE """
        elif self.current_performer_ids:
            where = f"""
                {where}
                AND {self._get_current_performer_ids()}
                AND ptp.directly_status != '{DirectlyStatus.DELETED}'
                AND pt.is_deleted IS FALSE
            """
        elif self.current_performer_group_ids:
            where = f"""
                {where}
                AND {self._get_current_performer_group_ids()}
                AND ptp.directly_status != '{DirectlyStatus.DELETED}'
                AND pt.is_deleted IS FALSE
            """

        if self.status is not None:
            where = f'{where} AND pw.status = %(status)s'

        return where

    def _get_from(self):
        result = """
        FROM processes_workflow pw
            LEFT JOIN processes_template t ON t.id = pw.template_id
            LEFT JOIN processes_workflow_owners ptra
              ON pw.id = ptra.workflow_id
            LEFT JOIN accounts_user au ON au.id = ptra.user_id
        """
        if self.current_performer_ids or self.current_performer_group_ids:
            result += f"""
            INNER JOIN processes_task pt
              ON pw.id = pt.workflow_id
                AND pt.status = '{TaskStatus.ACTIVE}'
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
              'user' AS type,
              -1 AS source_id,
              COUNT(workflow_id) AS workflows_count
            FROM main
            WHERE is_external IS TRUE
        UNION
        SELECT
              'user' AS type,
              workflow_starter_id AS source_id,
              COUNT(workflow_id) AS workflows_count
            FROM main
            WHERE is_external IS FALSE
            GROUP BY source_id
        ORDER BY source_id ASC
        """

    def get_sql(self):
        sql = self._get_inner_sql()
        return sql, self.params


class WorkflowCountsByCPerformerQuery(
    SqlQueryObject,
):

    def __init__(
        self,
        user_id: int,
        account_id: int,
        is_external: Optional[bool] = None,
        template_ids: Optional[List[int]] = None,
        template_task_api_names: Optional[List[int]] = None,
        workflow_starter_ids: Optional[List[int]] = None,
    ):
        self.status = WorkflowStatus.RUNNING
        self.params = {
            'user_id': user_id,
            'account_id': account_id,
            'status': self.status,
        }
        self.is_external = is_external
        # Works for running workflows only
        self.template_ids = template_ids
        self.template_task_api_names = template_task_api_names
        self.workflow_starter_ids = workflow_starter_ids

    def _get_template_ids(self):
        result, params = self._to_sql_list(
            values=self.template_ids,
            prefix='template_id',
        )
        self.params.update(params)
        return f"pw.template_id in {result}"

    def _get_template_task_api_names(self):
        result, params = self._to_sql_list(
            values=self.template_task_api_names,
            prefix='template_task_api_names',
        )
        self.params.update(params)
        return f"pt.api_name in {result}"

    def _get_workflow_starter_ids(self):
        result, params = self._to_sql_list(
            values=self.workflow_starter_ids,
            prefix='workflow_starter_id',
        )
        self.params.update(params)
        return f"pw.workflow_starter_id in {result}"

    def _get_is_external(self):
        self.params.update({'is_external': self.is_external})
        return 'pw.is_external = %(is_external)s'

    def _get_inner_where(self):
        where = f"""
            WHERE au.is_deleted IS FALSE
            AND pw.is_deleted IS FALSE
            AND pw.account_id = %(account_id)s
            AND ptra.user_id = %(user_id)s
            AND ptp.directly_status != '{DirectlyStatus.DELETED}' """

        if self.template_ids:
            where = f'{where} AND {self._get_template_ids()}'

        if self.template_task_api_names:
            where = (
                f'{where} AND {self._get_template_task_api_names()}'
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
        return f"""
        FROM processes_workflow pw
            LEFT JOIN processes_workflow_owners ptra
              ON pw.id = ptra.workflow_id
            LEFT JOIN accounts_user au ON au.id = ptra.user_id
            INNER JOIN processes_task pt
              ON pw.id = pt.workflow_id
                AND pt.status = '{TaskStatus.ACTIVE}'
            INNER JOIN processes_taskperformer ptp
              ON pt.id = ptp.task_id
        """

    def _get_inner_sql(self):
        return f"""
        WITH
        -- For users, we take into account both
        -- the direct purpose and through the group
        user_workflows AS (
            SELECT DISTINCT
                ptp.user_id AS user_id,
                pw.id AS workflow_id
            {self._get_from()}
            {self._get_inner_where()}

            UNION

            SELECT DISTINCT
                aug.user_id AS user_id,
                pw.id AS workflow_id
            FROM processes_workflow pw
                LEFT JOIN processes_workflow_owners ptra
                  ON pw.id = ptra.workflow_id
                LEFT JOIN accounts_user au ON au.id = ptra.user_id
                INNER JOIN processes_task pt
                  ON pw.id = pt.workflow_id
                    AND pt.status = '{TaskStatus.ACTIVE}'
                INNER JOIN processes_taskperformer ptp
                  ON pt.id = ptp.task_id
                INNER JOIN accounts_usergroup_users aug
                  ON ptp.group_id = aug.usergroup_id
                INNER JOIN accounts_usergroup ag
                  ON aug.usergroup_id = ag.id
            WHERE au.is_deleted IS FALSE
                AND pw.is_deleted IS FALSE
                AND pw.account_id = %(account_id)s
                AND ptra.user_id = %(user_id)s
                AND ptp.directly_status != '{DirectlyStatus.DELETED}'
                AND ag.is_deleted IS FALSE
                AND ptp.group_id IS NOT NULL
                {self._build_conditional_wheres()}
        ),
        -- For groups, we take into account cases when the group is explicitly
        -- assigned or the users of the group are assigned as direct performers
        group_workflows AS (
            -- Cases when the group is explicitly assigned
            SELECT DISTINCT
                ptp.group_id AS group_id,
                pw.id AS workflow_id
            FROM processes_workflow pw
                LEFT JOIN processes_workflow_owners ptra
                  ON pw.id = ptra.workflow_id
                LEFT JOIN accounts_user au ON au.id = ptra.user_id
                INNER JOIN processes_task pt
                  ON pw.id = pt.workflow_id
                    AND pt.status = '{TaskStatus.ACTIVE}'
                INNER JOIN processes_taskperformer ptp
                  ON pt.id = ptp.task_id
                INNER JOIN accounts_usergroup ag
                  ON ptp.group_id = ag.id
            WHERE au.is_deleted IS FALSE
                AND pw.is_deleted IS FALSE
                AND pw.account_id = %(account_id)s
                AND ptra.user_id = %(user_id)s
                AND ptp.directly_status != '{DirectlyStatus.DELETED}'
                AND ag.is_deleted IS FALSE
                AND ptp.group_id IS NOT NULL
                {self._build_conditional_wheres()}
        )

        SELECT
            'user' AS type,
            user_id AS source_id,
            COUNT(workflow_id) AS workflows_count
        FROM user_workflows
        WHERE user_id IS NOT NULL
        GROUP BY user_id

        UNION ALL

        SELECT
            'group' AS type,
            group_id AS source_id,
            COUNT(workflow_id) AS workflows_count
        FROM group_workflows
        WHERE group_id IS NOT NULL
        GROUP BY group_id
        ORDER BY type, source_id ASC
        """

    def _build_conditional_wheres(self):
        conditions = []

        if self.template_ids:
            conditions.append(f"{self._get_template_ids()}")

        if self.template_task_api_names:
            conditions.append(
                f"{self._get_template_task_api_names()}"
                f" AND pt.is_deleted IS FALSE",
            )

        if self.workflow_starter_ids and self.is_external:
            conditions.append(
                f"({self._get_workflow_starter_ids()}"
                f" OR {self._get_is_external()})",
            )
        elif self.workflow_starter_ids:
            conditions.append(f"{self._get_workflow_starter_ids()}")
        elif self.is_external is not None:
            conditions.append(f"{self._get_is_external()}")

        if self.status is not None:
            conditions.append("pw.status = %(status)s")

        if conditions:
            return "AND " + " AND ".join(conditions)
        return ""

    def get_sql(self):
        sql = self._get_inner_sql()
        return sql, self.params


class WorkflowCountsByTemplateTaskQuery(
    SqlQueryObject,
    DereferencedOwnersMixin,
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
        current_performer_group_ids: Optional[List[int]] = None,
    ):
        self.status = WorkflowApiStatus.MAP[status] if status else None
        self.params = {
            'user_id': user_id,
            'account_id': account_id,
            'status': self.status,
        }
        self.is_external = is_external
        self.template_ids = template_ids
        self.workflow_starter_ids = workflow_starter_ids
        self.current_performer_ids = current_performer_ids

        if current_performer_ids:
            group_ids = (
                UserGroup.objects
                .filter(users__in=current_performer_ids)
                .values_list('id', flat=True)
            )
            if current_performer_group_ids:
                current_performer_group_ids = (
                    set(current_performer_group_ids) | set(group_ids)
                )
            else:
                current_performer_group_ids = set(group_ids)
        self.current_performer_group_ids = current_performer_group_ids

    def _get_template_ids(self):
        result, params = self._to_sql_list(
            values=self.template_ids,
            prefix='template_id',
        )
        self.params.update(params)
        return f"pw.template_id in {result}"

    def _get_current_performer_ids(self):
        result, params = self._to_sql_list(
            values=self.current_performer_ids,
            prefix='current_performer_id',
        )
        self.params.update(params)
        return f"ptp.user_id in {result}"

    def _get_current_performer_group_ids(self):
        result, params = self._to_sql_list(
            values=self.current_performer_group_ids,
            prefix='current_performer_group_ids',
        )
        self.params.update(params)
        return f"ptp.group_id in {result}"

    def _get_workflow_starter_ids(self):
        result, params = self._to_sql_list(
            values=self.workflow_starter_ids,
            prefix='workflow_starter_id',
        )
        self.params.update(params)
        return f"pw.workflow_starter_id in {result}"

    def _get_is_external(self):
        self.params.update({'is_external': self.is_external})
        return 'pw.is_external = %(is_external)s'

    def _get_cte_where(self):
        result, params = self._to_sql_list(
            values=TemplateType.TYPES_ONBOARDING,
            prefix='template_type',
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
                prefix='template_id',
            )
            self.params.update(params)
            where += f' AND t.id in {result}'
        return where

    def _get_inner_where(self):
        where = f"""
            WHERE pw.is_deleted IS FALSE
            AND pw.account_id = %(account_id)s
            AND ptp.directly_status != '{DirectlyStatus.DELETED}' """

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

        if self.current_performer_ids and self.current_performer_group_ids:
            where = f"""
                {where}
                AND (
                    {self._get_current_performer_ids()}
                    OR
                    {self._get_current_performer_group_ids()}
                )
                AND ptp.directly_status != '{DirectlyStatus.DELETED}'
                AND pt.is_deleted IS FALSE
            """
        elif self.current_performer_ids:
            where = f"""
                {where}
                AND {self._get_current_performer_ids()}
                AND ptp.directly_status != '{DirectlyStatus.DELETED}'
                AND pt.is_deleted IS FALSE
            """
        elif self.current_performer_group_ids:
            where = f"""
                {where}
                AND {self._get_current_performer_group_ids()}
                AND ptp.directly_status != '{DirectlyStatus.DELETED}'
                AND pt.is_deleted IS FALSE
            """

        if self.status is not None:
            where = f'{where} AND pw.status = %(status)s'

        return where

    def _get_from(self):
        return f"""
        FROM processes_workflow pw
            INNER JOIN processes_task pt
              ON pw.id = pt.workflow_id
              AND pt.status = '{TaskStatus.ACTIVE}'
            INNER JOIN processes_taskperformer ptp
              ON pt.id = ptp.task_id
        """

    def _get_inner_sql(self):
        return f"""
        WITH
          dereferenced_owners AS ({self.dereferenced_owners()}),
          template_tasks AS (
            SELECT
              tt.id,
              tt.api_name,
              tt.number
            FROM processes_template t
              INNER JOIN processes_tasktemplate tt
                ON t.id = tt.template_id
                AND t.is_deleted IS FALSE
                AND tt.is_deleted IS FALSE
              INNER JOIN dereferenced_owners AS ptra
                ON t.id = ptra.template_id
              INNER JOIN accounts_user au ON au.id = ptra.user_id
            {self._get_cte_where()}
          ),
          result AS (
            SELECT
              template_task_api_name,
              COUNT(workflow_id) AS workflows_count
            FROM (
              SELECT
                pt.api_name AS template_task_api_name,
                pw.id AS workflow_id
              {self._get_from()}
              {self._get_inner_where()}
              GROUP BY
                pw.id,
                pt.api_name
            ) wf_by_template_tasks
            GROUP BY template_task_api_name
          )

        SELECT
          tt.id AS template_task_id,
          tt.api_name AS template_task_api_name,
          COALESCE(result.workflows_count, 0) AS workflows_count
        FROM template_tasks tt
          LEFT JOIN result ON tt.api_name = result.template_task_api_name
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
        template_task_api_name: Optional[str] = None,
        ordering: Optional[TaskOrdering] = None,
        assigned_to: Optional[int] = None,
        search: Optional[str] = None,
        is_completed: bool = False,
        **kwargs,
    ):

        """ Search string should be validated """

        self.template_id = template_id
        self.template_task_api_name = template_task_api_name
        self.ordering = ordering
        self.is_completed = bool(is_completed)
        self.assigned_to = user.id if assigned_to is None else assigned_to
        self.search_text = search
        self.params = {
            'account_id': user.account_id,
            'assigned_to': self.assigned_to,
        }

    def _get_search(self):
        tsquery, params = self._get_tsquery()
        self.params.update(params)
        return f"""
            {self._search_in(table='ps', field='content', tsquery=tsquery)}
        """

    def get_is_completed_where(self):
        if self.is_completed:
            return 'ptp.is_completed IS TRUE'
        return f"""
                pt.status = '{TaskStatus.ACTIVE}'
                AND ptp.is_completed IS FALSE
                AND pw.status = '{WorkflowStatus.RUNNING}'
            """

    def _get_template_task_api_name(self):
        self.params['template_task_api_name'] = self.template_task_api_name
        return 'pt.api_name = %(template_task_api_name)s'

    def _get_template_id(self):
        self.params['template_id'] = self.template_id
        return 't.id = %(template_id)s'

    def _get_inner_where(self):
        where = f"""
            WHERE pt.is_deleted IS FALSE
            AND pw.account_id = %(account_id)s
            AND (ptp.user_id = %(assigned_to)s OR aug.user_id IS NOT NULL)
            AND ptp.directly_status != '{DirectlyStatus.DELETED}'
            AND {self.get_is_completed_where()}
        """

        if self.search_text:
            where += f' AND {self._get_search()}'

        if self.template_task_api_name:
            where += f' AND {self._get_template_task_api_name()}'

        if self.template_id:
            where += f' AND {self._get_template_id()}'
        return where

    def _get_from(self):
        result = """
            FROM processes_task pt
            INNER JOIN processes_workflow pw ON (
              pw.id = pt.workflow_id AND
              pt.is_deleted IS FALSE
            )
            LEFT JOIN processes_taskperformer ptp ON (
              pt.id = ptp.task_id
            )
            LEFT JOIN accounts_usergroup_users aug ON (
              ptp.group_id = aug.usergroup_id AND
              aug.user_id = %(assigned_to)s
            )
            LEFT JOIN accounts_usergroup ag ON (
              ag.id = aug.usergroup_id AND
              ag.is_deleted IS FALSE
            )
        """
        if self.search_text:
            result += """
                LEFT JOIN processes_searchcontent ps (
                    pt.id = ps.task_id AND
                    ps.is_deleted IS FALSE
                )
            """
        if self.template_id:
            result += """
                LEFT JOIN processes_template t ON (
                  t.id = pw.template_id AND
                  t.is_deleted IS FALSE
                )
            """
        return result

    def _get_inner_sql(self):
        # TODO Remove in https://my.pneumatic.app/workflows/36988/
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
                pt.id as template_task_id,
                pt.api_name as template_task_api_name,
                pt.api_name,
                pt.is_urgent,
                pt.status
            {self._get_from()}
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
    DereferencedOwnersMixin,
):
    ordering_map = TemplateOrdering.MAP

    def __init__(
        self,
        user_id: int,
        account_id: int,
        ordering: Optional[str] = None,
        search_text: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_public: Optional[bool] = None,
    ):

        self.user_id = user_id
        self.account_id = account_id
        self.params = {
            'account_id': self.account_id,
            'user_id': user_id,
        }
        self.order = None
        self.is_active = is_active
        self.is_public = is_public
        self.ordering = ordering
        self.search_text = search_text

    def _get_search(self):
        tsquery, params = self._get_tsquery()
        self.params.update(params)
        return f"""
            (
                {self._search_in(table='ps', field='content', tsquery=tsquery)}
                OR {self._search_in(table='accounts_user', tsquery=tsquery)}
            )
        """

    def _get_allowed(self):
        self.params.update({'allowed_id': self.user_id})
        return """owners.user_id = %(allowed_id)s"""

    def _get_active(self):
        self.params.update({'is_active': self.is_active})
        return 'pt.is_active IS %(is_active)s'

    def _get_public(self):
        self.params.update({'is_public': self.is_public})
        return 'pt.is_public IS %(is_public)s'

    def _get_filter_by_type(self):
        result, params = self._to_sql_list(
            values=TemplateType.TYPES_ONBOARDING,
            prefix='template_type',
        )
        self.params.update(params)
        return f"pt.type NOT IN {result}"

    def get_workflows_select(self):
        if self.ordering in {
            TemplateOrdering.USAGE,
            TemplateOrdering.REVERSE_USAGE,
        }:
            return 'COUNT(DISTINCT workflows.id) AS workflows_count,'
        return ''

    def _get_from(self):
        result = """
        FROM processes_template pt
        LEFT JOIN processes_tasktemplate ptt ON (
          ptt.template_id = pt.id AND
          ptt.is_deleted = false
        )
        LEFT JOIN owners ON pt.id = owners.template_id
        LEFT JOIN accounts_user ON (
          owners.user_id = accounts_user.id AND
          accounts_user.is_deleted = false
        )
        """
        if self.search_text:
            result += """
                LEFT JOIN processes_searchcontent ps ON (
                    pt.id = ps.template_id AND
                    ps.is_deleted IS FALSE
                )
            """
        if self.ordering in {
            TemplateOrdering.USAGE,
            TemplateOrdering.REVERSE_USAGE,
        }:
            result += """
                LEFT JOIN processes_workflow workflows ON (
                  pt.id = workflows.template_id AND
                  workflows.is_deleted = FALSE
                )
            """
        return result

    def _get_inner_where(self):
        where = """
        WHERE pt.is_deleted = false AND
        pt.account_id = %(account_id)s AND
        accounts_user.id = %(user_id)s
        """

        where = (
            f'{where} AND {self._get_filter_by_type()} AND '
            f'{self._get_allowed()}'
        )

        if self.search_text:
            where = f'{where} AND {self._get_search()}'

        if self.is_active is not None:
            where = f'{where} AND {self._get_active()}'

        if self.is_public is not None:
            where = f'{where} AND {self._get_public()}'

        return where

    def _get_inner_sql(self):
        return f"""
        WITH owners AS ({self.dereferenced_owners()})
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
            {self.get_workflows_select()}
            COUNT(DISTINCT ptt.id) as tasks_count
        {self._get_from()}
        {self._get_inner_where()}
        GROUP BY pt.id
        """

    def get_sql(self):
        order_by = self.get_order_by(
            pre_columns='templates.is_active DESC',
            default_column='templates.id',
        )
        return f"""
        SELECT *
        FROM ({self._get_inner_sql()}) templates
        {order_by}
        """, self.params


class TemplateExportQuery(
    SqlQueryObject,
    OrderByMixin,
    DereferencedOwnersMixin,
):
    ordering_map = TemplateOrdering.MAP

    def __init__(
        self,
        user_id: int,
        account_id: int,
        ordering: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_public: Optional[bool] = None,
        owners_ids: Optional[List[int]] = None,
        owners_group_ids: Optional[List[int]] = None,
    ):

        self.user_id = user_id
        self.account_id = account_id
        self.params = {
            'account_id': self.account_id,
            'user_id': user_id,
        }
        self.order = None
        self.is_active = is_active
        self.is_public = is_public
        self.owners_ids = owners_ids
        self.owners_group_ids = owners_group_ids
        self.ordering = ordering

    def _get_owners_ids(self):
        result, params = self._to_sql_list(
            values=self.owners_ids,
            prefix='owners_ids',
        )
        self.params.update(params)
        return f'pto.user_id in {result}'

    def _get_owners_group_ids(self):
        result, params = self._to_sql_list(
            values=self.owners_group_ids,
            prefix='owners_group_ids',
        )
        self.params.update(params)
        return f'pto.group_id in {result}'

    def _get_active(self):
        self.params.update({'is_active': self.is_active})
        return 't.is_active IS %(is_active)s'

    def _get_public(self):
        self.params.update({'is_public': self.is_public})
        return 't.is_public IS %(is_public)s'

    def _get_filter_by_type(self):
        result, params = self._to_sql_list(
            values=TemplateType.TYPES_ONBOARDING,
            prefix='template_type',
        )
        self.params.update(params)
        return f"t.type NOT IN {result}"

    def _get_inner_where(self):
        where = """
            WHERE t.is_deleted = false AND
            t.account_id = %(account_id)s
        """

        where = f'{where} AND {self._get_filter_by_type()}'

        if self.is_active is not None:
            where = f'{where} AND {self._get_active()}'

        if self.is_public is not None:
            where = f'{where} AND {self._get_public()}'

        if self.owners_ids and self.owners_group_ids:
            where = (
                f'{where} AND'
                f' ({self._get_owners_ids()}'
                f' OR {self._get_owners_group_ids()})'
            )
        elif self.owners_ids:
            where = (
                f'{where} AND {self._get_owners_ids()}'
            )
        elif self.owners_group_ids:
            where = (
                f'{where} AND {self._get_owners_group_ids()}'
            )

        return where

    def _get_inner_sql(self):
        return f"""
            WITH owners AS ({self.dereferenced_owners()})
            SELECT t.*
            FROM processes_template t
            JOIN processes_templateowner pto
              ON t.id = pto.template_id
            LEFT JOIN owners ON t.id = owners.template_id
            {self._get_inner_where()}
        """

    def get_sql(self):
        order_by = self.get_order_by(
            pre_columns='templates.is_active DESC',
            default_column='templates.id',
        )
        return f"""
            SELECT DISTINCT *
            FROM ({self._get_inner_sql()}) templates
            {order_by}
        """, self.params


class RunningTaskTemplateQuery(SqlQueryObject):
    def __init__(self, template_id: int, user_id: int):
        self._template_id = template_id
        self._user_id = user_id

    def get_sql(self):
        return f"""
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
            ptp.directly_status != '{DirectlyStatus.DELETED}'
          WHERE ptt.is_deleted IS FALSE AND
            ptt.template_id = %(template_id)s AND
            pt.is_deleted IS FALSE AND
            pt.date_started IS NOT NULL AND
            pt.status != 'completed'
          ORDER BY ptt.number;
        """, {
            'user_id': self._user_id,
            'template_id': self._template_id,
            'running_status': WorkflowStatus.RUNNING,
        }


class TemplateStepsQuery(
    SqlQueryObject,
    DereferencedOwnersMixin,
    DereferencedPerformersMixin,
):

    def __init__(
        self,
        user: User,
        template_id: int,
        with_tasks_in_progress: Optional[bool] = None,
    ):

        self.with_tasks_in_progress = with_tasks_in_progress
        self.params = {
            'account_id': user.account.id,
            'user_id': user.id,
            'template_id': template_id,
        }

    def _get_from(self):
        result = """
            FROM processes_template t
              JOIN processes_tasktemplate ptt
                ON ptt.template_id = t.id"""
        if self.with_tasks_in_progress is None:
            result += f"""
                JOIN ({self.dereferenced_owners()}) dereferenced_owners
                  ON dereferenced_owners.template_id = t.id"""
        else:
            result += f"""
                JOIN processes_task pt
                  ON ptt.api_name = pt.api_name
                JOIN processes_workflow pw
                  ON pt.workflow_id = pw.id
                JOIN ({self.dereferenced_performers()}) dereferenced_performers
                  ON pt.id = dereferenced_performers.task_id """
        return result

    def _get_filter_by_type(self):
        result, params = self._to_sql_list(
            values=TemplateType.TYPES_ONBOARDING,
            prefix='template_type',
        )
        self.params.update(params)
        return f"t.type NOT IN {result}"

    def _get_where(self):
        result = f"""
            WHERE ptt.is_deleted IS FALSE
            AND t.is_deleted IS FALSE
            AND t.id = %(template_id)s
            AND t.account_id = %(account_id)s
            AND {self._get_filter_by_type()}"""
        if self.with_tasks_in_progress is True:
            result += f"""
                AND pt.is_deleted IS FALSE
                AND dereferenced_performers.is_completed IS FALSE
                AND pt.status = '{TaskStatus.ACTIVE}'
                AND pw.status = {WorkflowStatus.RUNNING}"""
        elif self.with_tasks_in_progress is False:
            result += """
                AND pt.is_deleted IS FALSE
                AND dereferenced_performers.is_completed IS TRUE"""
        return result

    def get_sql(self):
        return f"""
            SELECT DISTINCT
              ptt.id,
              ptt.name,
              ptt.number,
              ptt.api_name
              {self._get_from()}
              {self._get_where()}
            ORDER BY ptt.number;
        """, self.params


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
        current_performer_ids: Optional[List[int]] = None,
        current_performer_group_ids: Optional[List[int]] = None,
        date_before_tsp: Optional[datetime] = None,
        date_after_tsp: Optional[datetime] = None,
    ):

        # TODO Refactoring need

        from rest_framework.exceptions import ValidationError

        self.sql_params = {'account_id': account_id, 'user_id': user_id}

        if templates is not None:
            try:
                self.templates = literal_eval(templates)
            except (SyntaxError, ValueError) as ex:
                raise ValidationError(MSG_PW_0024('templates')) from ex

        if current_performer_ids is not None:
            try:
                self.users = current_performer_ids
                if isinstance(self.users, int):
                    self.users = (self.users,)
            except (SyntaxError, ValueError) as ex:
                raise ValidationError(MSG_PW_0024('users')) from ex

        if current_performer_group_ids is not None:
            group_users_ids = (
                UserModel.objects
                .on_account(account_id=account_id)
                .get_users_in_groups(group_ids=current_performer_group_ids)
                .user_ids_set()
            )
            if group_users_ids:
                if current_performer_ids:
                    self.users = list(set(self.users) | group_users_ids)
                else:
                    self.users = list(group_users_ids)

        if date_before_tsp is not None:
            self.date_before_tsp = date_before_tsp

        if date_after_tsp is not None:
            self.date_after_tsp = date_after_tsp

    def get_sql(self):
        subquery = """
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
        LEFT JOIN processes_workflow_owners workflow_owners ON
          workflow.id = workflow_owners.workflow_id
        WHERE
          NOT we.is_deleted AND
          we.account_id = %(account_id)s AND
          NOT workflow.is_deleted AND
          NOT template.is_deleted AND
          workflow_owners.user_id = %(user_id)s
        """
        ordering = 'ORDER BY we.created DESC, we.id DESC'
        sub_ordering = ' ORDER BY we.workflow_id, we.created DESC'
        additional_where = []
        where = []

        result, params = self._to_sql_list(self.event_types, 'type')
        self.sql_params.update(params)
        additional_where.append(
            f'we.type in {result}',
        )

        if hasattr(self, 'users'):
            result, params = self._to_sql_list(self.users, 'user')
            self.sql_params.update(params)
            additional_where.append(
                f'we.user_id in {result}',
            )

        if hasattr(self, 'templates'):
            result, params = self._to_sql_list(self.templates, 'template')
            self.sql_params.update(params)
            additional_where.append(
                f'workflow.template_id in {result}',
            )

        if hasattr(self, 'date_before_tsp'):
            self.sql_params['date_before_tsp'] = self.date_before_tsp
            where.append('we.created <= %(date_before_tsp)s')

        if hasattr(self, 'date_after_tsp'):
            self.sql_params['date_after_tsp'] = self.date_after_tsp
            where.append('we.created >= %(date_after_tsp)s')

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
        actions_ids: List[int],
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
        WorkflowEventType.TASK_PERFORMER_GROUP_CREATED,
        WorkflowEventType.TASK_PERFORMER_GROUP_DELETED,
        WorkflowEventType.FORCE_DELAY,
        WorkflowEventType.FORCE_RESUME,
        WorkflowEventType.DUE_DATE_CHANGED,
        WorkflowEventType.SUB_WORKFLOW_RUN,
    ]

    def __init__(
        self,
        user: UserModel,
        date_from_tsp: Optional[datetime] = None,
        date_to_tsp: Optional[datetime] = None,
    ):

        self.date_before = date_from_tsp
        self.date_after = date_to_tsp
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
            prefix='event_type',
        )
        self.params.update(event_params)
        template_types, template_params = self._to_sql_list(
            values=TemplateType.TYPES_ONBOARDING,
            prefix='template_type',
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


class TemplateTitlesQuery(SqlQueryObject, DereferencedPerformersMixin):

    def __init__(
        self,
        user: User,
        with_tasks_in_progress: Optional[bool] = None,
        workflows_status: Optional[WorkflowStatus] = None,
    ):
        self.params = {
            'account_id': user.account.id,
            'user_id': user.id,
        }
        self.with_tasks_in_progress = with_tasks_in_progress
        if workflows_status:
            self.status = WorkflowApiStatus.MAP[workflows_status]
            self.params['status'] = self.status
        else:
            self.status = None

    def _get_from(self):
        result = """
            FROM processes_template AS t
              INNER JOIN processes_workflow pw
                ON t.id = pw.template_id """
        if self.with_tasks_in_progress is None:
            result += """
                INNER JOIN processes_workflow_owners pto
                  ON pw.id = pto.workflow_id AND pto.user_id = %(user_id)s"""
        else:
            result += f"""
                INNER JOIN processes_task pt
                  ON pw.id = pt.workflow_id
                JOIN ({self.dereferenced_performers()}) dereferenced_performers
                  ON pt.id = dereferenced_performers.task_id"""
        return result

    def _get_filter_by_type(self):
        result, params = self._to_sql_list(
            values=TemplateType.TYPES_ONBOARDING,
            prefix='template_type',
        )
        self.params.update(params)
        return f"t.type NOT IN {result}"

    def _get_where(self):
        result = f"""
            WHERE t.is_deleted IS FALSE
              AND t.account_id = %(account_id)s
              AND pw.is_deleted IS FALSE
              AND {self._get_filter_by_type()}"""
        if self.with_tasks_in_progress is True:
            result += f"""
                AND pt.is_deleted IS FALSE
                AND dereferenced_performers.is_completed IS FALSE
                AND pt.status = '{TaskStatus.ACTIVE}'
                AND pw.status = {WorkflowStatus.RUNNING}"""
        elif self.with_tasks_in_progress is False:
            result += """
                AND pt.is_deleted IS FALSE
                AND dereferenced_performers.is_completed IS TRUE"""
        elif self.status is not None:
            result += "AND pw.status = %(status)s"
        return result

    def get_sql(self) -> Tuple[str, dict]:
        return f"""
            SELECT
              t.id,
              t.name,
              COUNT(DISTINCT pw.id) AS workflows_count
            {self._get_from()}
            {self._get_where()}
            GROUP BY t.id
            ORDER BY workflows_count DESC, t.name ASC
        """, self.params


class UpdateWorkflowOwnersQuery(
    SqlQueryObject,
    SearchSqlQueryMixin,
    OrderByMixin,
    DereferencedOwnersMixin,
):

    def __init__(
        self,
        template_id: int,
    ):
        self.params = {
            'template_id': template_id,
        }

    def get_sql(self) -> Tuple[str, dict]:
        pass

    def insert_sql(self):
        return f"""
            WITH
              all_owners AS ({self.dereferenced_owners_by_template_id()})
            INSERT INTO processes_workflow_owners (workflow_id, user_id)
            SELECT
                pw.id AS workflow_id,
                ao.user_id AS user_id
            FROM processes_workflow pw
            JOIN all_owners ao
              ON pw.template_id = ao.template_id
            WHERE pw.is_deleted = false;
        """, self.params


class UpdateWorkflowMemberQuery(
    SqlQueryObject,
    SearchSqlQueryMixin,
    OrderByMixin,
    DereferencedOwnersMixin,
):

    def __init__(
        self,
        template_id: int,
    ):

        self.params = {
            'template_id': template_id,
        }

    def get_sql(self) -> Tuple[str, dict]:
        pass

    def insert_sql(self):
        return f"""
            WITH all_users AS (
              SELECT pw.id AS workflow_id, ao.user_id AS user_id
              FROM processes_workflow pw
              JOIN ({self.dereferenced_owners_by_template_id()}) ao
                ON pw.template_id = ao.template_id
              WHERE pw.is_deleted = false
              UNION
              {self.task_performers_by_template_id()}
            )
            INSERT INTO processes_workflow_members (workflow_id, user_id)
            SELECT
              au.workflow_id,
              au.user_id
            FROM all_users au
            LEFT JOIN processes_workflow_members pwm
              ON pwm.workflow_id = au.workflow_id
              AND pwm.user_id = au.user_id
            WHERE pwm.workflow_id IS NULL;
        """, self.params
