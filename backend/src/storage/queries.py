from typing import Dict, Any, Optional
from django.contrib.auth import get_user_model

from src.generics.paginations import DefaultPagination
from src.queries import SqlQueryObject
from src.storage.enums import AccessType
from src.storage.models import Attachment

UserModel = get_user_model()


class AttachmentListQuery(SqlQueryObject):
    """
    Class for building an SQL query to retrieve
    all attachments accessible to the user.
    Single SQL with joins: no extra Python queries for permission or groups.
    """

    def __init__(
        self,
        user: UserModel,
        limit: Optional[int] = DefaultPagination.default_limit,
        offset: Optional[int] = None,
        task_id: Optional[int] = None,
        workflow_id: Optional[int] = None,
        current_account_only: bool = False,
    ):
        """
        List attachments the user may open.

        Optional filters: task, workflow, and (for MCP) the current
        account only. Permission and groups stay in SQL.
        """
        self.user = user
        self.limit = limit
        self.offset = offset
        self.filters: list[str] = []
        self.params: Dict[str, Any] = {
            'user_id': user.id,
            'account_id': user.account_id,
            'limit': limit,
            'access_account': AccessType.ACCOUNT,
            'access_public': AccessType.PUBLIC,
        }
        if task_id is not None:
            self.filters.append('AND a.task_id = %(task_id)s')
            self.params['task_id'] = task_id
        if workflow_id is not None:
            self.filters.append('AND a.workflow_id = %(workflow_id)s')
            self.params['workflow_id'] = workflow_id
        if current_account_only:
            self.filters.append('AND a.account_id = %(account_id)s')

    def _get_where(self) -> str:
        """
        WHERE with EXISTS; permission via join, groups via subquery.
        """
        permissions = """
            WHERE a.is_deleted = FALSE
            AND (
                EXISTS (
                    SELECT 1
                    FROM permissions_userobjectpermission uop
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
                (a.account_id = %(account_id)s
                 AND a.access_type = %(access_account)s)
                OR
                a.access_type = %(access_public)s
            )
        """
        return permissions + '\n' + '\n'.join(self.filters)

    def _get_offset(self) -> str:
        """Returns OFFSET clause if offset is provided."""
        if self.offset:
            self.params['offset'] = self.offset
            return "OFFSET %(offset)s"
        return ""

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
            SELECT DISTINCT ON (a.file_id) {fields}
            FROM storage_attachment a
            {self._get_where()}
            ORDER BY a.file_id, a.id DESC
        """
        # Wrap to apply pagination with the desired final ordering
        sql = f"""
            SELECT * FROM ({sql}) sub
            ORDER BY sub.id DESC
            LIMIT %(limit)s {self._get_offset()}
        """
        return sql, self.params

    def get_count_sql(self) -> str:
        """
        Returns SQL query for counting total attachments.
        """
        return f"""
            SELECT
                1 AS id,
                COUNT(DISTINCT a.file_id) AS count
            FROM storage_attachment a
            {self._get_where()}
        """
