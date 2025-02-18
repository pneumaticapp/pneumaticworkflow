class DereferencedOwnersMixin:
    @staticmethod
    def dereferenced_owners():
        return f"""
            SELECT pto.template_id, g.user_id AS user_id
            FROM processes_templateowner AS pto
            JOIN accounts_usergroup_users AS g
              ON g.usergroup_id = pto.group_id
            WHERE pto.type = 'group' AND g.user_id = %(user_id)s
            UNION
            SELECT pto.template_id, pto.user_id
            FROM processes_templateowner AS pto
            WHERE pto.type = 'user' AND pto.user_id = %(user_id)s
        """

    @staticmethod
    def dereferenced_owners_by_template_id():
        """ Selects unique template_id and user_id pairs
            (returns all template owner, either user_id, or via group__user_id)
            for template_id"""

        return f"""
            SELECT DISTINCT
              pto.template_id,
              COALESCE(pto.user_id, ug.user_id) AS user_id
            FROM processes_templateowner pto
            LEFT JOIN accounts_usergroup_users ug
              ON pto.type = 'group' AND pto.group_id = ug.usergroup_id
            WHERE pto.template_id = %(template_id)s
              AND (pto.type = 'user' OR pto.type = 'group')
        """
