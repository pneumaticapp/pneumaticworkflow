from pneumatic_backend.queries import SqlQueryObject
from pneumatic_backend.accounts.enums import (
    UserType,
    UserStatus
)
from pneumatic_backend.processes.enums import (
    DirectlyStatus,
    WorkflowStatus
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
            'user_type': UserType.GUEST,
            'user_status': UserStatus.ACTIVE,
            'task_id': task_id,
            'account_id': account_id,
            'directly_status': DirectlyStatus.DELETED
        }

    def _get_wf_filter(self):
        result, params = self._to_sql_list(
            values=WorkflowStatus.END_STATUSES,
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
            AND au.type = %(user_type)s
            AND au.is_active IS TRUE
            AND au.status = %(user_status)s
            AND au.account_id = %(account_id)s
            AND pw.account_id = %(account_id)s
            AND ptp.task_id = %(task_id)s
            AND pw.current_task >= pt.number
            AND ptp.directly_status != %(directly_status)s
            AND {self._get_wf_filter()}
        """, self.params
