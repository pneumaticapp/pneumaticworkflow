from typing import Dict, Any

from src.storage.models import Attachment
from src.queries import SqlQueryObject


class AttachmentListQuery(SqlQueryObject):
    """
    Class for building an SQL query to retrieve
    all attachments accessible to the user.
    Single SQL with joins: no extra Python queries for permission or groups.
    """

    def __init__(self, user):
        """
        Initialization with the user.
        Only user_id and account_id are needed; permission and groups in SQL.
        """
        self.user = user
        self.params: Dict[str, Any] = {
            'user_id': user.id,
            'account_id': user.account_id,
        }

    def _get_where(self) -> str:
        """
        WHERE with EXISTS; permission via join, groups via subquery.
        """
        return """
            WHERE a.is_deleted = FALSE
            AND (
                EXISTS (
                    SELECT 1
                    FROM guardian_userobjectpermission uop
                    JOIN auth_permission p ON uop.permission_id = p.id
                    JOIN django_content_type ct ON p.content_type_id = ct.id
                    WHERE uop.user_id = %(user_id)s
                    AND ct.app_label = 'storage'
                    AND ct.model = 'attachment'
                    AND p.codename = 'access_attachment'
                    AND uop.object_pk = a.id::text
                )
                OR
                EXISTS (
                    SELECT 1
                    FROM permissions_groupobjectpermission gop
                    JOIN auth_permission p ON gop.permission_id = p.id
                    JOIN django_content_type ct ON p.content_type_id = ct.id
                    WHERE gop.group_id IN (
                        SELECT ug_users.usergroup_id
                        FROM accounts_usergroup_users ug_users
                        WHERE ug_users.user_id = %(user_id)s
                    )
                    AND ct.app_label = 'storage'
                    AND ct.model = 'attachment'
                    AND p.codename = 'access_attachment'
                    AND gop.object_pk = a.id::text
                )
                OR
                (a.account_id = %(account_id)s AND a.access_type = 'account')
                OR
                a.access_type = 'public'
            )
        """

    def get_sql(self) -> tuple:
        """
        Returns (sql, params) for listing attachments.
        """
        field_mappings = []
        for field in Attachment._meta.fields:
            if hasattr(field, 'column'):
                db_column = field.column
            else:
                db_column = field.name
            field_mappings.append(f'a.{db_column}')
        fields = ', '.join(field_mappings)
        sql = f"""
            SELECT {fields}
            FROM storage_attachment a
            {self._get_where()}
        """
        return sql, self.params
