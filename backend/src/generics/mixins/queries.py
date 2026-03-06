from src.processes.enums import DirectlyStatus, PerformerType


class DereferencedOwnersMixin:
    @staticmethod
    def dereferenced_owners():
        return """
            SELECT pto.template_id, g.user_id AS user_id
            FROM processes_templateowner AS pto
            JOIN accounts_usergroup_users AS g
              ON g.usergroup_id = pto.group_id
            WHERE pto.type = 'group'
              AND pto.is_deleted IS FALSE
              AND g.user_id = %(user_id)s
            UNION
            SELECT pto.template_id, pto.user_id
            FROM processes_templateowner AS pto
            WHERE pto.type = 'user'
              AND pto.is_deleted IS FALSE
              AND pto.user_id = %(user_id)s
        """

    @staticmethod
    def dereferenced_owners_by_template_id():
        """ Selects unique template_id and user_id pairs
            (returns all template owner, either user_id, or via group__user_id)
            for template_id"""

        return """
            SELECT DISTINCT
              pto.template_id,
              COALESCE(pto.user_id, ug.user_id) AS user_id
            FROM processes_templateowner pto
            LEFT JOIN accounts_usergroup_users ug
              ON pto.type = 'group' AND pto.group_id = ug.usergroup_id
            WHERE pto.template_id = %(template_id)s
              AND pto.is_deleted IS FALSE
              AND COALESCE(pto.user_id, ug.user_id) IS NOT NULL
        """

    @staticmethod
    def task_performers_by_template_id():
        """
        Returns workflow_id and user_id for task performers
        (groups and users) linked to a template, excluding directly_status=1.
        """
        return """
            SELECT DISTINCT
              pt.workflow_id,
              COALESCE(ug.user_id, ptp.user_id) AS user_id
            FROM processes_taskperformer ptp
              JOIN processes_task pt ON ptp.task_id = pt.id
              JOIN processes_workflow pw ON pt.workflow_id = pw.id
              AND pw.template_id = %(template_id)s
              LEFT JOIN accounts_usergroup_users ug
              ON ptp.group_id = ug.usergroup_id AND ptp.type = 'group'
            WHERE ptp.directly_status != 1
              AND ptp.is_deleted IS FALSE
              AND pt.is_deleted IS FALSE
              AND pw.is_deleted IS FALSE
              AND COALESCE(ug.user_id, ptp.user_id) IS NOT NULL
        """


class DereferencedPerformersMixin:

    @staticmethod
    def dereferenced_performers():

        """ Convert group performers to users and return it """

        return f"""
            SELECT DISTINCT ON (user_id, ptp.task_id)
              (
                CASE
                  WHEN ptp.type = '{PerformerType.GROUP}' THEN g.user_id
                  ELSE ptp.user_id
                END
              ) AS user_id,
              ptp.task_id,
              ptp.is_completed
            FROM processes_taskperformer ptp
            LEFT JOIN accounts_usergroup_users g
              ON g.usergroup_id = ptp.group_id
            WHERE
              ptp.is_deleted IS FALSE
              AND ptp.directly_status != '{DirectlyStatus.DELETED}'
              AND (
                ptp.type = '{PerformerType.GROUP}'
                AND g.user_id = %(user_id)s
              )
              OR (
                ptp.type = '{PerformerType.USER}'
                AND ptp.user_id = %(user_id)s
              )
        """

    @staticmethod
    def all_dereferenced_performers():

        """ Convert group performers to users and return it (for any user) """

        return f"""
            SELECT DISTINCT ON (user_id, ptp.task_id)
              (
                CASE
                  WHEN ptp.type = '{PerformerType.GROUP}' THEN g.user_id
                  ELSE ptp.user_id
                END
              ) AS user_id,
              ptp.task_id,
              ptp.is_completed
            FROM processes_taskperformer ptp
            LEFT JOIN accounts_usergroup_users g
              ON g.usergroup_id = ptp.group_id
            WHERE
              ptp.is_deleted IS FALSE
              AND ptp.directly_status != '{DirectlyStatus.DELETED}'
        """
