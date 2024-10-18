from pneumatic_backend.accounts.enums import (
    NotificationStatus,
    NotificationType,
    UserStatus
)
from pneumatic_backend.processes.enums import FieldType
from pneumatic_backend.queries import SqlQueryObject


class CountTemplatesByUserQuery(SqlQueryObject):

    """ Returns the numbers of active templates and workflows
        that the user is a member of """

    def __init__(self, user_id: int, account_id: int):
        self.user_id = user_id
        self.account_id = account_id

    def _get_params(self):
        return {
            'user_id': self.user_id,
            'account_id': self.account_id,
        }

    def get_sql(self):
        return """
          SELECT count(*) FROM (
            SELECT DISTINCT ON (pt.id) pt.id FROM processes_template pt
            JOIN processes_template_template_owners pwra
              ON pt.id = pwra.template_id
            JOIN processes_tasktemplate ptw ON pt.id = ptw.template_id
            JOIN processes_rawperformertemplate prpt
              ON ptw.id = prpt.task_id
          WHERE pt.is_deleted IS FALSE AND
            pt.account_id = %(account_id)s AND
            pt.is_active IS TRUE AND
            ptw.is_deleted IS FALSE AND
            (pwra.user_id = %(user_id)s OR prpt.user_id = %(user_id)s)
          ) pt_by_user
          UNION ALL
          SELECT count(*) FROM (
            SELECT DISTINCT ON (w.id) w.id FROM
              processes_workflow w
            JOIN processes_task pt ON w.id = pt.workflow_id
            JOIN processes_taskperformer ptp ON pt.id = ptp.task_id
            WHERE
              w.is_deleted IS FALSE AND
              pt.is_deleted IS FALSE AND
              w.account_id = %(account_id)s AND
              user_id = %(user_id)s
          ) workflows_by_user;
        """, self._get_params()


class DeleteUserFromRawPerformerTemplateQuery(SqlQueryObject):
    def __init__(
        self,
        user_to_delete: int,
        user_to_substitution: int,
    ):
        self.user_to_delete = user_to_delete
        self.user_to_substitution = user_to_substitution

    def get_sql(self):
        return """
        DELETE FROM processes_rawperformertemplate
        WHERE
          user_id = %(user_to_delete)s AND
          task_id IN (
            SELECT task_id FROM processes_rawperformertemplate
            WHERE user_id = %(user_to_substitution)s
            AND is_deleted IS FALSE
          )
        """, {
            'user_to_delete': self.user_to_delete,
            'user_to_substitution': self.user_to_substitution,
        }


class DeleteUserFromRawPerformerQuery(SqlQueryObject):
    def __init__(
        self,
        user_to_delete: int,
        user_to_substitution: int,
    ):
        self.user_to_delete = user_to_delete
        self.user_to_substitution = user_to_substitution

    def get_sql(self):
        return """
        DELETE FROM processes_rawperformer
        WHERE
          user_id = %(user_to_delete)s AND
          task_id IN (
            SELECT task_id FROM processes_rawperformer
            WHERE user_id = %(user_to_substitution)s
              AND is_deleted IS FALSE
          )
        """, {
            'user_to_delete': self.user_to_delete,
            'user_to_substitution': self.user_to_substitution,
        }


class DeleteUserFromTaskPerformerQuery(SqlQueryObject):
    def __init__(
        self,
        user_to_delete: int,
        user_to_substitution: int,
    ):
        self.user_to_delete = user_to_delete
        self.user_to_substitution = user_to_substitution

    def get_sql(self):
        return """
        DELETE FROM processes_taskperformer
        WHERE
          user_id = %(user_to_delete)s AND
          task_id IN (
            SELECT task_id FROM processes_taskperformer
            WHERE user_id = %(user_to_substitution)s
          )
        """, {
            'user_to_delete': self.user_to_delete,
            'user_to_substitution': self.user_to_substitution,
        }


class DeleteUserFromTemplateOwnerQuery(SqlQueryObject):
    def __init__(
        self,
        user_to_delete: int,
        user_to_substitution: int,
    ):
        self.user_to_delete = user_to_delete
        self.user_to_substitution = user_to_substitution

    def get_sql(self):
        return """
        DELETE FROM processes_template_template_owners
        WHERE
          user_id = %(user_to_delete)s AND
          template_id IN (
            SELECT template_id FROM processes_template_template_owners
            WHERE user_id = %(user_to_substitution)s
          )
        """, {
            'user_to_delete': self.user_to_delete,
            'user_to_substitution': self.user_to_substitution,
        }


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
