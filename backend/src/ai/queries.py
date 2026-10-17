from typing import Tuple

from src.ai.enums import AIAgentActionType
from src.generics.mixins.queries import DereferencedPerformersMixin
from src.processes.enums import TaskStatus, WorkflowStatus
from src.queries import SqlQueryObject


class AIAgentNewTasksQuery(SqlQueryObject, DereferencedPerformersMixin):

    """ The active tasks of the running workflows assigned to the active
        AI agents directly or as a group member, which the agent has not
        completed and whose every run since the task start failed,
        until the failures reach max_run_failures """

    def __init__(self, max_run_failures: int):
        self._max_run_failures = max_run_failures

    def get_sql(self) -> Tuple[str, dict]:
        return f"""
          SELECT
            performers.task_id,
            ag.id AS agent_id
          FROM ({self.all_dereferenced_performers()}) performers
          JOIN ai_aiagent ag ON ag.user_id = performers.user_id
            AND ag.is_active IS TRUE
            AND ag.is_deleted IS FALSE
          JOIN processes_task pt ON pt.id = performers.task_id
            AND pt.is_deleted IS FALSE
            AND pt.status = %(task_status)s
          JOIN processes_workflow pw ON pw.id = pt.workflow_id
            AND pw.is_deleted IS FALSE
            AND pw.status = %(workflow_status)s
          LEFT JOIN ai_aiagentaction aa ON aa.agent_id = ag.id
            AND aa.task_id = pt.id
            AND aa.action IN (%(in_progress)s, %(failed)s)
            AND aa.date_created >= pt.date_started
          WHERE performers.is_completed IS FALSE
          GROUP BY performers.task_id, ag.id
          HAVING
            COUNT(aa.id) FILTER (WHERE aa.action = %(in_progress)s)
            = COUNT(aa.id) FILTER (WHERE aa.action = %(failed)s)
            AND COUNT(aa.id) FILTER (WHERE aa.action = %(in_progress)s)
            < %(max_run_failures)s
          ORDER BY performers.task_id, ag.id
        """, {
            'task_status': TaskStatus.ACTIVE,
            'workflow_status': WorkflowStatus.RUNNING,
            'in_progress': AIAgentActionType.TASK_IN_PROGRESS,
            'failed': AIAgentActionType.TASK_FAILED,
            'max_run_failures': self._max_run_failures,
        }
