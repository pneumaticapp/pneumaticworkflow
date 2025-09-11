from src.queries import SqlQueryObject
from src.accounts.enums import (
    UserType,
    UserStatus
)
from src.processes.enums import (
    DirectlyStatus,
    WorkflowStatus, TaskStatus
)


class GetGuestQuery(SqlQueryObject):

    def __init__(
        self,
        user_id: int,
        task_id: int,
        account_id: int
    ):
        self.params = {
            'user_id': user_id,
            'task_id': task_id,
            'account_id': account_id,
        }

    def _get_wf_filter(self):
        result, params = self._to_sql_list(
            values=WorkflowStatus.DONE,
            prefix='wf_status'
        )
        self.params.update(params)
        return f'pw.status NOT IN {result}'

    def get_sql(self):
        return f"""
        SELECT au.*
        FROM accounts_user au
            INNER JOIN processes_taskperformer ptp ON au.id = ptp.user_id
            INNER JOIN processes_task pt ON ptp.task_id = pt.id
            INNER JOIN processes_workflow pw ON pt.workflow_id = pw.id
        WHERE
            au.is_deleted = False
            AND au.id = %(user_id)s
            AND au.type = '{UserType.GUEST}'
            AND au.is_active IS TRUE
            AND au.status = '{UserStatus.ACTIVE}'
            AND au.account_id = %(account_id)s
            AND pw.account_id = %(account_id)s
            AND ptp.task_id = %(task_id)s
            AND pt.status = '{TaskStatus.ACTIVE}'
            AND ptp.directly_status != '{DirectlyStatus.DELETED}'
            AND {self._get_wf_filter()}
        """, self.params
