from abc import abstractmethod
from typing import List

from src.accounts.enums import (
    NotificationStatus,
    NotificationType,
    UserStatus,
)
from src.processes.enums import (
    DirectlyStatus,
    FieldType,
    PerformerType,
    TaskStatus,
    WorkflowStatus,
)
from src.queries import SqlQueryObject


class CountTemplatesByUserQuery(SqlQueryObject):

    """ Returns the numbers of active templates and workflows
        that the user is a member of """

    def __init__(self, user_id: int, account_id: int):
        self.user_id = user_id
        self.account_id = account_id
        self.params = {
            'user_id': user_id,
            'account_id': account_id,
        }

    def get_sql(self):
        return """
          SELECT count(*) FROM (
            SELECT DISTINCT ON (t.id) t.id FROM processes_template t
            JOIN processes_templateowner AS pto
              ON t.id = pto.template_id
            JOIN processes_tasktemplate ptt ON t.id = ptt.template_id
            JOIN processes_rawperformertemplate prpt
              ON ptt.id = prpt.task_id
          WHERE t.is_deleted IS FALSE AND
            t.account_id = %(account_id)s AND
            t.is_active IS TRUE AND
            ptt.is_deleted IS FALSE AND
            (prpt.user_id = %(user_id)s OR
            pto.user_id = %(user_id)s)
          ) pt_by_user
          UNION ALL
          SELECT count(*) FROM (
            SELECT DISTINCT ON (pw.id) pw.id
            FROM processes_workflow pw
            JOIN processes_task pt ON pw.id = pt.workflow_id
            JOIN processes_taskperformer ptp ON pt.id = ptp.task_id
            WHERE
              pw.is_deleted IS FALSE AND
              pt.is_deleted IS FALSE AND
              pw.account_id = %(account_id)s AND
              user_id = %(user_id)s
          ) workflows_by_user;
        """, self.params


class CountTemplatesByGroupQuery(SqlQueryObject):

    """ Returns the numbers of active templates and workflows
        that the group is a member of """

    def __init__(self, group_id: int, account_id: int):
        self.group_id = group_id
        self.account_id = account_id
        self.params = {
            'group_id': group_id,
            'account_id': account_id,
        }

    def get_sql(self):
        return """
          SELECT count(*) FROM (
            SELECT DISTINCT ON (t.id) t.id FROM processes_template t
            JOIN processes_templateowner AS pto
              ON t.id = pto.template_id
            JOIN processes_tasktemplate ptt ON t.id = ptt.template_id
            JOIN processes_rawperformertemplate prpt
              ON ptt.id = prpt.task_id
          WHERE t.is_deleted IS FALSE AND
            t.account_id = %(account_id)s AND
            t.is_active IS TRUE AND
            ptt.is_deleted IS FALSE AND
            (prpt.group_id = %(group_id)s OR
            pto.group_id = %(group_id)s)
          ) pt_by_group
          UNION ALL
          SELECT count(*) FROM (
            SELECT DISTINCT ON (pw.id) pw.id
            FROM processes_workflow pw
            JOIN processes_task pt ON pw.id = pt.workflow_id
            JOIN processes_taskperformer ptp ON pt.id = ptp.task_id
            WHERE
              pw.is_deleted IS FALSE AND
              pt.is_deleted IS FALSE AND
              pw.account_id = %(account_id)s AND
              group_id = %(group_id)s
          ) workflows_by_group;
        """, self.params


class BaseDeleteRawPerformerTemplateQuery(SqlQueryObject):
    def __init__(self, delete_id: int, substitution_id: int):
        self.delete_id = delete_id
        self.substitution_id = substitution_id
        self.params = {
            'delete_id': delete_id,
            'substitution_id': substitution_id,
        }

    @abstractmethod
    def delete_field(self) -> str:
        pass

    @abstractmethod
    def substitution_field(self) -> str:
        pass

    def get_sql(self):
        return f"""
        DELETE FROM processes_rawperformertemplate
        WHERE
          {self.substitution_field} = %(substitution_id)s AND
          task_id IN (
            SELECT task_id FROM processes_rawperformertemplate
            WHERE {self.delete_field} = %(delete_id)s
              AND is_deleted IS FALSE
          )
        """, self.params


class DeleteGroupFromRawPerformerTemplateQuery(
    BaseDeleteRawPerformerTemplateQuery,
):
    delete_field = "group_id"
    substitution_field = "group_id"


class DeleteGroupUserFromRawPerformerTemplateQuery(
    BaseDeleteRawPerformerTemplateQuery,
):
    delete_field = "group_id"
    substitution_field = "user_id"


class DeleteUserGroupFromRawPerformerTemplateQuery(
    BaseDeleteRawPerformerTemplateQuery,
):
    delete_field = "user_id"
    substitution_field = "group_id"


class DeleteUserFromRawPerformerTemplateQuery(
    BaseDeleteRawPerformerTemplateQuery,
):
    delete_field = "user_id"
    substitution_field = "user_id"


class BaseDeleteRawPerformerQuery(SqlQueryObject):
    def __init__(self, delete_id: int, substitution_id: int):
        self.delete_id = delete_id
        self.substitution_id = substitution_id
        self.params = {
            'delete_id': delete_id,
            'substitution_id': substitution_id,
        }

    @abstractmethod
    def delete_field(self) -> str:
        pass

    @abstractmethod
    def substitution_field(self) -> str:
        pass

    def get_sql(self):
        return f"""
        DELETE FROM processes_rawperformer
        WHERE
          {self.substitution_field} = %(substitution_id)s AND
          task_id IN (
            SELECT task_id FROM processes_rawperformer
            WHERE {self.delete_field} = %(delete_id)s
              AND is_deleted IS FALSE
          )
        """, self.params


class DeleteGroupFromRawPerformerQuery(BaseDeleteRawPerformerQuery):
    delete_field = "group_id"
    substitution_field = "group_id"


class DeleteGroupUserFromRawPerformerQuery(BaseDeleteRawPerformerQuery):
    delete_field = "group_id"
    substitution_field = "user_id"


class DeleteUserGroupFromRawPerformerQuery(BaseDeleteRawPerformerQuery):
    delete_field = "user_id"
    substitution_field = "group_id"


class DeleteUserFromRawPerformerQuery(BaseDeleteRawPerformerQuery):
    delete_field = "user_id"
    substitution_field = "user_id"


class BaseDeleteTaskPerformerQuery(SqlQueryObject):
    def __init__(self, delete_id: int, substitution_id: int):
        self.delete_id = delete_id
        self.substitution_id = substitution_id
        self.params = {
            'delete_id': delete_id,
            'substitution_id': substitution_id,
        }

    @abstractmethod
    def delete_field(self) -> str:
        pass

    @abstractmethod
    def substitution_field(self) -> str:
        pass

    def get_sql(self):
        return f"""
        DELETE FROM processes_taskperformer
        WHERE
          {self.substitution_field} = %(substitution_id)s AND
          task_id IN (
            SELECT task_id FROM processes_taskperformer
            WHERE {self.delete_field} = %(delete_id)s
            AND task_id IN (
                SELECT id FROM processes_task
                WHERE status != 'completed'
            )
          )
        """, self.params


class DeleteGroupFromTaskPerformerQuery(BaseDeleteTaskPerformerQuery):
    delete_field = "group_id"
    substitution_field = "group_id"


class DeleteGroupUserFromTaskPerformerQuery(BaseDeleteTaskPerformerQuery):
    delete_field = "group_id"
    substitution_field = "user_id"


class DeleteUserGroupFromTaskPerformerQuery(BaseDeleteTaskPerformerQuery):
    delete_field = "user_id"
    substitution_field = "group_id"


class DeleteUserFromTaskPerformerQuery(BaseDeleteTaskPerformerQuery):
    delete_field = "user_id"
    substitution_field = "user_id"


class BaseDeleteTemplateOwnerQuery(SqlQueryObject):
    def __init__(self, delete_id: int, substitution_id: int):
        self.delete_id = delete_id
        self.substitution_id = substitution_id
        self.params = {
            'delete_id': delete_id,
            'substitution_id': substitution_id,
        }

    @abstractmethod
    def delete_field(self) -> str:
        pass

    @abstractmethod
    def substitution_field(self) -> str:
        pass

    def get_sql(self):
        return f"""
        DELETE FROM processes_templateowner
        WHERE
          {self.substitution_field} = %(substitution_id)s AND
          template_id IN (
            SELECT template_id FROM processes_templateowner
            WHERE {self.delete_field} = %(delete_id)s
          )
        """, self.params


class DeleteGroupFromTemplateOwnerQuery(BaseDeleteTemplateOwnerQuery):
    delete_field = "group_id"
    substitution_field = "group_id"


class DeleteGroupUserFromTemplateOwnerQuery(BaseDeleteTemplateOwnerQuery):
    delete_field = "group_id"
    substitution_field = "user_id"


class DeleteUserGroupFromTemplateOwnerQuery(BaseDeleteTemplateOwnerQuery):
    delete_field = "user_id"
    substitution_field = "group_id"


class DeleteUserFromTemplateOwnerQuery(BaseDeleteTemplateOwnerQuery):
    delete_field = "user_id"
    substitution_field = "user_id"


class DeleteUserFromWorkflowMembersQuery(SqlQueryObject):

    """ Deletes membership records for user_to_delete
        where user_to_substitution exists in workflow """

    def __init__(
        self,
        user_to_delete: int,
        user_to_substitution: int,
    ):
        self.user_to_delete = user_to_delete
        self.user_to_substitution = user_to_substitution

    def get_sql(self):
        return """
        DELETE FROM processes_workflow_members
        WHERE
          user_id = %(user_to_delete)s AND
          workflow_id IN (
            SELECT workflow_id FROM processes_workflow_members
            WHERE user_id = %(user_to_substitution)s
          )
        """, {
            'user_to_delete': self.user_to_delete,
            'user_to_substitution': self.user_to_substitution,
        }


class DeleteUserFromWorkflowOwnersQuery(SqlQueryObject):

    """ Deletes ownership records for user_to_delete
        where user_to_substitution exists in workflow """

    def __init__(
        self,
        user_to_delete: int,
        user_to_substitution: int,
    ):
        self.user_to_delete = user_to_delete
        self.user_to_substitution = user_to_substitution

    def get_sql(self):
        return """
        DELETE FROM processes_workflow_owners
        WHERE
          user_id = %(user_to_delete)s AND
          workflow_id IN (
            SELECT workflow_id FROM processes_workflow_owners
            WHERE user_id = %(user_to_substitution)s
          )
        """, {
            'user_to_delete': self.user_to_delete,
            'user_to_substitution': self.user_to_substitution,
        }


class DeleteUserFromTemplateConditionsQuery(SqlQueryObject):

    """ Deletes conditions in template for user_to_delete
        where user_to_substitution exists in conditions """

    def __init__(
        self,
        user_to_delete: str,
        user_to_substitution: str,
    ):
        self.user_to_delete = user_to_delete
        self.user_to_substitution = user_to_substitution

    def get_sql(self):
        return """
        DELETE FROM processes_predicatetemplate
        WHERE
          field_type = %(field_type)s AND
          value = %(user_to_delete)s AND
          (rule_id, operator) IN (
            SELECT rule_id, operator
            FROM processes_predicatetemplate
            WHERE
              field_type = %(field_type)s AND
              value = %(user_to_substitution)s
          )
        """, {
            'field_type': FieldType.USER,
            'user_to_delete': self.user_to_delete,
            'user_to_substitution': self.user_to_substitution,
        }


class DeleteUserFromConditionsQuery(SqlQueryObject):

    """ Deletes conditions in workflow for user_to_delete
        where user_to_substitution exists in conditions """

    def __init__(
        self,
        user_to_delete: str,
        user_to_substitution: str,
    ):
        self.user_to_delete = user_to_delete
        self.user_to_substitution = user_to_substitution

    def get_sql(self):
        return """
        DELETE FROM processes_predicate
        WHERE
          field_type = %(field_type)s AND
          value = %(user_to_delete)s AND
          (rule_id, operator) IN (
            SELECT rule_id, operator
            FROM processes_predicate
            WHERE
              field_type = %(field_type)s AND
              value = %(user_to_substitution)s
          )
        """, {
            'field_type': FieldType.USER,
            'user_to_delete': self.user_to_delete,
            'user_to_substitution': self.user_to_substitution,
        }


class CreateSystemNotificationsQuery(SqlQueryObject):
    def __init__(self, system_message):
        self._system_message = system_message

    def get_sql(self):
        return """
          INSERT INTO accounts_notification (
            account_id,
            is_deleted,
            text,
            type,
            status,
            datetime,
            system_message_id,
            user_id,
            is_notified_about_not_read
          )
          SELECT
            au.account_id,
            false,
            %(text)s,
            %(type)s,
            %(status)s,
            %(publication_date)s,
            %(system_message_id)s,
            au.id,
            FALSE
          FROM accounts_user au
          LEFT JOIN accounts_notification an on au.id = an.user_id AND
            an.system_message_id = %(system_message_id)s
          WHERE au.is_deleted IS FALSE
            AND au.status = %(user_status)s
            AND an.id IS NULL
        """, {
            'text': self._system_message.text,
            'type': NotificationType.SYSTEM,
            'status': NotificationStatus.NEW,
            'publication_date': self._system_message.publication_date,
            'system_message_id': self._system_message.id,
            'user_status': UserStatus.ACTIVE,
        }


class FetchGroupTaskNotificationRecipientsQuery(SqlQueryObject):

    def __init__(
        self,
        group_id: int,
        user_ids: List[int],
        account_id: int,
    ):
        self.group_id = group_id
        self.account_id = account_id
        self.user_ids = user_ids
        self.params = {
            'group_id': group_id,
            'account_id': account_id,
        }

    def _get_user_ids(self):
        result, params = self._to_sql_list(
            values=self.user_ids,
            prefix='user',
        )
        self.params.update(params)
        return result

    def _get_notify_users(self):

        """ Returns tasks by target users where the group is performer """

        return f"""
        SELECT DISTINCT
          au.id AS id,
          au.email AS email,
          au.is_new_tasks_subscriber AS is_subscribed,
          pt.id AS task_id
        FROM accounts_user au
        INNER JOIN accounts_usergroup aug ON aug.id = %(group_id)s
        INNER JOIN processes_taskperformer ptp ON ptp.group_id = aug.id
        INNER JOIN processes_task pt ON pt.id = ptp.task_id
        INNER JOIN processes_workflow pw ON pw.id = pt.workflow_id
        WHERE au.id IN {self._get_user_ids()}
          AND au.account_id = %(account_id)s
          AND au.is_deleted IS FALSE
          AND aug.is_deleted IS FALSE
          AND ptp.type = '{PerformerType.GROUP}'
          AND ptp.directly_status != '{DirectlyStatus.DELETED}'
          AND ptp.is_deleted IS FALSE
          AND ptp.is_completed IS FALSE
          AND pt.status = '{TaskStatus.ACTIVE}'
          AND pt.is_deleted IS FALSE
          AND pw.status = {WorkflowStatus.RUNNING}
        """

    def _get_not_empty_groups_table(self):

        """ Return other account groups performers containing target users """

        return f"""
        SELECT
          accounts_usergroup.id,
          accounts_usergroup_users.user_id,
          COUNT(accounts_usergroup_users.user_id) OVER (
            PARTITION BY accounts_usergroup_users.user_id IS NOT NULL
          ) AS users_count
        FROM accounts_usergroup
        INNER JOIN accounts_usergroup_users
          ON accounts_usergroup_users.usergroup_id = accounts_usergroup.id
        WHERE accounts_usergroup.is_deleted IS FALSE
          AND accounts_usergroup.account_id = %(account_id)s
          AND accounts_usergroup.id != %(group_id)s
          AND accounts_usergroup_users.user_id IN {self._get_user_ids()}
        """

    def get_sql(self):

        """ Check that notify user are not performers on task in another ways:
            - if the user is an performer via another group
            - if the user is an performer on task directly
        """

        return f"""
          SELECT DISTINCT
            notify_users.id,
            notify_users.email,
            notify_users.is_subscribed,
            notify_users.task_id
          FROM (
            {self._get_notify_users()}
          ) AS notify_users
          LEFT JOIN (
            {self._get_not_empty_groups_table()}
          ) AS g ON g.user_id = notify_users.id
          LEFT JOIN processes_taskperformer existent_performer
            ON (
              (
                existent_performer.type = '{PerformerType.USER}'
                AND existent_performer.user_id = notify_users.id
              ) OR (
                existent_performer.type = '{PerformerType.GROUP}'
                AND existent_performer.group_id = g.id
              )
            )
            AND existent_performer.task_id = notify_users.task_id
            AND existent_performer.directly_status
             != '{DirectlyStatus.DELETED}'
            AND existent_performer.is_deleted IS FALSE
        WHERE
        existent_performer.id IS NULL

        """, self.params
