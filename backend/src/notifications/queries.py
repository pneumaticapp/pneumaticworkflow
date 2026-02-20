from typing import Tuple

from django.contrib.auth import get_user_model

from src.accounts.enums import NotificationType, UserStatus
from src.generics.mixins.queries import DereferencedPerformersMixin
from src.notifications.enums import NotificationMethod
from src.processes.enums import (
    DirectlyStatus,
    TaskStatus,
    WorkflowStatus,
)
from src.queries import (
    SqlQueryObject,
)

UserModel = get_user_model()


class UsersWithOverdueTaskQuery(SqlQueryObject):

    def get_sql(self) -> Tuple[str, dict]:
        return f"""
        SELECT DISTINCT ON (user_id, task_id)
          result.user_id,
          result.user_email,
          result.user_type,
          result.workflow_id,
          result.workflow_name,
          result.task_id,
          result.task_name,
          result.account_id,
          result.template_name,
          result.workflow_starter_id,
          au.first_name AS workflow_starter_first_name,
          au.last_name AS workflow_starter_last_name,
          aa.logo_lg,
          aa.log_api_requests as logging
        FROM (
            SELECT
              au.id AS user_id,
              au.email AS user_email,
              au.type AS user_type,
              au.account_id,
              pw.id AS workflow_id,
              pw.name AS workflow_name,
              (
                CASE
                  WHEN pw.is_legacy_template IS TRUE
                    OR t.id IS NULL
                  THEN pw.legacy_template_name
                  ELSE t.name
                END
              ) AS template_name,
              pw.workflow_starter_id,
              pt.id AS task_id,
              pt.name AS task_name,
              an.id AS notification
            FROM processes_workflow pw
            LEFT JOIN processes_template t
              ON pw.template_id = t.id
              AND pw.is_legacy_template IS FALSE
              AND t.is_deleted is FALSE
            INNER JOIN processes_task pt
              ON pw.id = pt.workflow_id
              AND pt.status = '{TaskStatus.ACTIVE}'
            INNER JOIN processes_taskperformer ptp
              ON pt.id = ptp.task_id
            INNER JOIN accounts_user au
              ON au.id = ptp.user_id
            INNER JOIN accounts_account aa
              ON au.account_id = aa.id
            LEFT JOIN accounts_notification an
              ON an.task_id = pt.id
              AND an.user_id = ptp.user_id
              AND an.type = '{NotificationType.OVERDUE_TASK}'
            WHERE pt.is_deleted is FALSE
              AND pw.status = '{WorkflowStatus.RUNNING}'
              AND pt.due_date IS NOT NULL
              AND pt.due_date <= NOW()
              AND ptp.is_completed IS FALSE
              AND ptp.directly_status != '{DirectlyStatus.DELETED}'
              AND au.status = '{UserStatus.ACTIVE}'
        ) result INNER JOIN accounts_user au
          ON au.id = result.workflow_starter_id
        INNER JOIN accounts_account aa
          ON aa.id = au.account_id
        WHERE notification is NULL
        ORDER BY user_id, task_id, account_id
        """, {}


class UsersWithRemainderTaskQuery(SqlQueryObject, DereferencedPerformersMixin):

    def get_sql(self) -> Tuple[str, dict]:
        result = f"""
        SELECT
          au.id AS user_id,
          au.email AS user_email,
          au.type AS user_type,
          pt.id AS task_id,
          aa.id AS account_id,
          aa.logo_lg,
          aa.log_api_requests AS logging,
          '{NotificationMethod.task_reminder}' AS method_name,
          TRUE as sync,
          COUNT(pt.id) AS count
        FROM processes_workflow pw
          INNER JOIN processes_task pt
            ON pt.workflow_id = pw.id
        INNER JOIN (
          {self.all_dereferenced_performers()}
        ) dereferenced_performers
            ON pt.id = dereferenced_performers.task_id
          INNER JOIN accounts_user au
            ON au.id = dereferenced_performers.user_id
          INNER JOIN accounts_account aa
            ON au.account_id = aa.id
        WHERE
          pw.is_deleted = FALSE
          AND pw.status = '{WorkflowStatus.RUNNING}'
          AND pw.reminder_notification = TRUE
          AND pw.is_deleted = FALSE
          AND pt.status = '{TaskStatus.ACTIVE}'
          AND dereferenced_performers.is_completed IS FALSE
          AND au.status = '{UserStatus.ACTIVE}'
        GROUP BY au.id, pt.id, aa.id
        ORDER BY au.id
        """
        return result, {}
