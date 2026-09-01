from typing import List

from django.contrib.auth import get_user_model

from src.permissions.entities import ObjectPermissionData
from src.permissions.enums import PermissionObjectType
from src.permissions.exceptions import (
    UserObjectPermissionServiceException,
)
from src.permissions.messages import MSG_PM_0001
from src.processes.models.workflows.workflow import Workflow

UserModel = get_user_model()


class UserObjectPermissionService:

    """Effective permissions of a user on account objects.

    Mirrors the checks performed by the API permission classes
    (``WorkflowMemberOrViewerPermission`` for view and
    ``WorkflowOwnerPermission`` for change) so that clients can
    ask in bulk what the current user may do with a set of objects.
    """

    def __init__(self, user: UserModel) -> None:
        self.user = user

    def _get_workflow_permissions(
        self,
        obj_ids: List[int],
    ) -> List[ObjectPermissionData]:
        user = self.user
        qst = Workflow.objects.on_account(user.account_id).by_ids(obj_ids)
        if user.is_account_owner:
            view_ids = set(qst.values_list('id', flat=True))
            change_ids = view_ids
        else:
            view_ids = set(
                qst.with_view_access(user.id).values_list('id', flat=True),
            )
            change_ids = (
                set(
                    qst.with_change_access(user.id).values_list(
                        'id',
                        flat=True,
                    ),
                )
                if user.is_admin else set()
            )
        return [
            ObjectPermissionData(
                id=obj_id,
                has_view=obj_id in view_ids,
                has_change=obj_id in change_ids,
            )
            for obj_id in obj_ids
        ]

    def get_permissions(
        self,
        obj_type: PermissionObjectType.LITERALS,
        obj_ids: List[int],
    ) -> List[ObjectPermissionData]:
        """Return permissions for each id in the request order.

        Response format:
            [{'id': int, 'has_view': bool, 'has_change': bool}, ...]

        Duplicate ids are collapsed into a single entry.
        Ids that do not exist or belong to another account are
        reported with all permissions set to ``False`` instead of
        failing the whole batch: the client maps the result by id
        and must not lose the rest of the list because of one
        stale id.

        Raises:
            UserObjectPermissionServiceException: unsupported obj_type.
        """
        if obj_type != PermissionObjectType.WORKFLOW:
            raise UserObjectPermissionServiceException(
                MSG_PM_0001(obj_type),
            )
        return self._get_workflow_permissions(list(dict.fromkeys(obj_ids)))
