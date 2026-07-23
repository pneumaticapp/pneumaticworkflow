from collections import defaultdict
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Set

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils.functional import cached_property

from src.accounts.models import UserGroup
from src.permissions.enums import PermissionSource
from src.permissions.models import UserObjectPermission
from src.processes.enums import (
    DirectlyStatus,
    PerformerType,
    WorkflowPermission,
)
from src.processes.models.workflows.task import Task, TaskPerformer

UserModel = get_user_model()

if TYPE_CHECKING:
    from src.processes.models.workflows.workflow import Workflow


class WorkflowPermissionService:
    """Unified permission management for Workflow objects.

    Replaces workflow.members and workflow.owners M2M fields
    with Guardian object-level permissions backed by a custom
    ``UserObjectPermission`` model that supports source tracking.

    Each permission row records *why* it was granted (``source_type``
    and ``source_id``) so permissions can be revoked surgically
    when the source is removed (e.g. a comment is deleted or a
    performer is removed) instead of doing a full recalculation.

    Permissions:
        view_workflow — read access (replaces members M2M)
        change_workflow — lifecycle actions + edit: resume, snooze,
                          finish, return_to, edit name/description
                          (replaces owners M2M)
    """

    def __init__(self, workflow: 'Workflow'):
        self.workflow = workflow
        self._ct = self._get_content_type()
        self._object_pk = str(workflow.pk)

    @classmethod
    def _get_content_type(cls) -> ContentType:
        """Get Workflow ContentType (Django caches internally)."""
        workflow_model = apps.get_model('processes', 'Workflow')
        return ContentType.objects.get_for_model(workflow_model)

    def _filter_account_user_ids(
        self,
        user_ids: Iterable[int],
    ) -> List[int]:
        """Keep only users that belong to the workflow account."""
        ids = [uid for uid in user_ids if uid is not None]
        if not ids:
            return []
        return list(
            UserModel.objects.filter(
                id__in=ids,
                account_id=self.workflow.account_id,
            ).values_list('id', flat=True),
        )

    @cached_property
    def _view_perm(self) -> Permission:
        return Permission.objects.get(
            codename=WorkflowPermission.VIEW,
            content_type=self._ct,
        )

    @cached_property
    def _change_perm(self) -> Permission:
        return Permission.objects.get(
            codename=WorkflowPermission.CHANGE,
            content_type=self._ct,
        )

    def grant_view(
        self,
        user: UserModel,
        source_type: PermissionSource.LITERALS,
        source_id: int,
    ):
        """Grant view access to a single user, tagged with source.

        Replaces: workflow.members.add(user)
        """
        if user.account_id != self.workflow.account_id:
            return
        # ignore_conflicts: skip if this exact source-permission already exists
        UserObjectPermission.objects.bulk_create(
            [UserObjectPermission(
                user=user,
                permission=self._view_perm,
                content_type=self._ct,
                object_pk=self._object_pk,
                source_type=source_type,
                source_id=source_id,
            )],
            ignore_conflicts=True,
        )

    def grant_change(
        self,
        user: UserModel,
        source_type: PermissionSource.LITERALS,
        source_id: int,
    ):
        """Grant change + view access to a single user.

        Replaces: workflow.owners.add(user)
        Change implies view — owner can always see their workflow.
        """
        if user.account_id != self.workflow.account_id:
            return
        UserObjectPermission.objects.bulk_create(
            [
                UserObjectPermission(
                    user=user,
                    permission=perm,
                    content_type=self._ct,
                    object_pk=self._object_pk,
                    source_type=source_type,
                    source_id=source_id,
                )
                for perm in (self._view_perm, self._change_perm)
            ],
            ignore_conflicts=True,
        )

    def grant_view_bulk(
        self,
        user_ids: Iterable[int],
        source_type: PermissionSource.LITERALS,
        source_id: int,
    ):
        """Bulk-grant view access, tagged with source.

        Replaces: workflow.members.add(*user_ids)
        """
        user_ids = self._filter_account_user_ids(user_ids)
        if not user_ids:
            return
        perm = self._view_perm
        # ignore_conflicts: skip if this source-permission already exists
        UserObjectPermission.objects.bulk_create(
            [
                UserObjectPermission(
                    user_id=uid,
                    permission=perm,
                    content_type=self._ct,
                    object_pk=self._object_pk,
                    source_type=source_type,
                    source_id=source_id,
                )
                for uid in user_ids
            ],
            ignore_conflicts=True,
        )

    def revoke_view(
        self,
        source_type: PermissionSource.LITERALS,
        source_id: int,
    ):
        """Remove view permissions granted by a specific source.

        Only deletes rows matching the source — if the user has
        view access from another source (performer, owner, etc.)
        they keep it.
        """
        UserObjectPermission.objects.filter(
            permission=self._view_perm,
            content_type=self._ct,
            object_pk=self._object_pk,
            source_type=source_type,
            source_id=source_id,
        ).delete()

    def sync_view(
        self,
        user_ids: Iterable[int],
        source_type: PermissionSource.LITERALS,
        source_id: int,
    ) -> Set[int]:
        """Diff-based sync of view permissions for a given source.

        Compares the current set of users who hold a view permission
        from (source_type, source_id) against ``user_ids``:
        - users no longer desired are revoked,
        - users not yet present are granted,
        - users already present are left untouched.

        Returns:
            Set of user IDs that were actually granted.
            Callers can use this to send notifications only
            for truly new mentions.
        """
        desired = set(self._filter_account_user_ids(user_ids))

        current = set(
            UserObjectPermission.objects.filter(
                permission=self._view_perm,
                content_type=self._ct,
                object_pk=self._object_pk,
                source_type=source_type,
                source_id=source_id,
            ).values_list('user_id', flat=True),
        )

        to_remove = current - desired
        to_add = desired - current

        if to_remove:
            UserObjectPermission.objects.filter(
                permission=self._view_perm,
                content_type=self._ct,
                object_pk=self._object_pk,
                source_type=source_type,
                source_id=source_id,
                user_id__in=to_remove,
            ).delete()

        if to_add:
            perm = self._view_perm
            UserObjectPermission.objects.bulk_create(
                [
                    UserObjectPermission(
                        user_id=uid,
                        permission=perm,
                        content_type=self._ct,
                        object_pk=self._object_pk,
                        source_type=source_type,
                        source_id=source_id,
                    )
                    for uid in to_add
                ],
                ignore_conflicts=True,
            )

        return to_add

    @transaction.atomic
    def set_view_and_change(self, user_ids: Iterable[int]):
        """Replace change_workflow (+ matching TEMPLATE_OWNER view).

        Clears existing change perms and all TEMPLATE_OWNER view
        rows, then grants change + view to the new set.
        """
        change_perm = self._change_perm
        view_perm = self._view_perm
        source_id = self.workflow.template_id or 0
        # Dedupe while preserving order
        unique_ids = list(dict.fromkeys(
            self._filter_account_user_ids(user_ids),
        ))

        UserObjectPermission.objects.filter(
            permission=change_perm,
            content_type=self._ct,
            object_pk=self._object_pk,
        ).delete()

        # Drop every TEMPLATE_OWNER view row (any source_id) so
        # stale grants with a mismatched source_id cannot linger.
        UserObjectPermission.objects.filter(
            permission=view_perm,
            content_type=self._ct,
            object_pk=self._object_pk,
            source_type=PermissionSource.TEMPLATE_OWNER,
        ).delete()

        if not unique_ids:
            return

        objs = []
        for uid in unique_ids:
            for perm in (change_perm, view_perm):
                objs.append(UserObjectPermission(
                    user_id=uid,
                    permission=perm,
                    content_type=self._ct,
                    object_pk=self._object_pk,
                    source_type=PermissionSource.TEMPLATE_OWNER,
                    source_id=source_id,
                ))
        UserObjectPermission.objects.bulk_create(
            objs,
            ignore_conflicts=True,
        )

    @transaction.atomic
    def sync_performer_sources(self):
        """Align PERFORMER / PERFORMER_GROUP rows with TaskPerformer.

        Used after bulk reassignment where many performer rows change
        at once. Does not touch mention, vacation, template-owner,
        or legacy viewer sources.
        """
        # Task.objects excludes soft-deleted tasks (cascade soft-deletes
        # performers, but query via Task manager stays explicit/safe).
        task_ids = Task.objects.filter(
            workflow_id=self.workflow.id,
        ).values_list('id', flat=True)
        active_performers = (
            TaskPerformer.objects
            .filter(task_id__in=task_ids)
            .exclude(directly_status=DirectlyStatus.DELETED)
        )

        # USER performers → sync per task
        task_users: Dict[int, Set[int]] = defaultdict(set)
        for task_id, uid in (
            active_performers
            .filter(type=PerformerType.USER)
            .values_list('task_id', 'user_id')
        ):
            if uid is not None:
                task_users[task_id].add(uid)

        existing_performer_task_ids = set(
            UserObjectPermission.objects.filter(
                permission=self._view_perm,
                content_type=self._ct,
                object_pk=self._object_pk,
                source_type=PermissionSource.PERFORMER,
            ).values_list('source_id', flat=True),
        )
        for task_id in existing_performer_task_ids | set(task_users):
            self.sync_view(
                user_ids=task_users.get(task_id, set()),
                source_type=PermissionSource.PERFORMER,
                source_id=task_id,
            )

        # GROUP performers → sync per group
        group_ids = set(
            active_performers
            .filter(type=PerformerType.GROUP)
            .values_list('group_id', flat=True),
        )
        group_members: Dict[int, Set[int]] = defaultdict(set)
        if group_ids:
            for gid, uid in (
                UserGroup.include_personal
                .filter(id__in=group_ids, is_deleted=False)
                .values_list('id', 'users__id')
            ):
                if uid is not None:
                    group_members[gid].add(uid)

        existing_group_ids = set(
            UserObjectPermission.objects.filter(
                permission=self._view_perm,
                content_type=self._ct,
                object_pk=self._object_pk,
                source_type=PermissionSource.PERFORMER_GROUP,
            ).values_list('source_id', flat=True),
        )
        for gid in existing_group_ids | group_ids:
            self.sync_view(
                user_ids=group_members.get(gid, set()),
                source_type=PermissionSource.PERFORMER_GROUP,
                source_id=gid,
            )

    def sync_performer_group(
        self,
        group_id: int,
        member_ids: Optional[Iterable[int]] = None,
    ):
        """Sync or revoke PERFORMER_GROUP view for one group.

        If the group is still an active performer on any task of
        this workflow, align UOP with ``member_ids`` (or current
        group membership). Otherwise revoke the source entirely.
        """
        task_ids = Task.objects.filter(
            workflow_id=self.workflow.id,
        ).values_list('id', flat=True)
        still_on_workflow = (
            TaskPerformer.objects
            .filter(
                task_id__in=task_ids,
                type=PerformerType.GROUP,
                group_id=group_id,
            )
            .exclude(directly_status=DirectlyStatus.DELETED)
            .exists()
        )
        if not still_on_workflow:
            self.revoke_view(
                source_type=PermissionSource.PERFORMER_GROUP,
                source_id=group_id,
            )
            return

        if member_ids is None:
            member_ids = (
                UserGroup.include_personal
                .filter(id=group_id, is_deleted=False)
                .values_list('users__id', flat=True)
            )
        self.sync_view(
            user_ids=[uid for uid in member_ids if uid is not None],
            source_type=PermissionSource.PERFORMER_GROUP,
            source_id=group_id,
        )

    def has_view(self, user: UserModel) -> bool:
        """Check if user can view workflow.

        Uses direct UOP query instead of user.has_perm() because
        ObjectPermissionBackend's group check is incompatible with
        custom GroupObjectPermission model (UserGroup FK vs auth.Group).
        """
        return UserObjectPermission.objects.filter(
            user=user,
            permission=self._view_perm,
            content_type=self._ct,
            object_pk=self._object_pk,
        ).exists()

    def has_change(self, user: UserModel) -> bool:
        """Check if user can manage workflow lifecycle.

        Uses direct UOP query instead of user.has_perm() because
        ObjectPermissionBackend's group check is incompatible with
        custom GroupObjectPermission model (UserGroup FK vs auth.Group).
        """
        return UserObjectPermission.objects.filter(
            user=user,
            permission=self._change_perm,
            content_type=self._ct,
            object_pk=self._object_pk,
        ).exists()

    def get_users_with_view(self) -> Set[int]:
        """Get all user IDs who can view this workflow.

        Replaces: workflow.members.values_list('id', flat=True)
        Used for deduplication in mention notifications.
        """
        return set(
            UserObjectPermission.objects.filter(
                permission=self._view_perm,
                content_type=self._ct,
                object_pk=self._object_pk,
            ).values_list('user_id', flat=True),
        )

    def get_users_with_change(self) -> List[int]:
        """Get sorted list of user IDs with change_workflow.

        Replaces: workflow.owners.values_list('id', flat=True)
        Used by API serializers to populate the 'owners' response field.
        """
        return sorted(
            UserObjectPermission.objects.filter(
                permission=self._change_perm,
                content_type=self._ct,
                object_pk=self._object_pk,
            ).values_list('user_id', flat=True).distinct(),
        )

    @staticmethod
    def get_users_with_change_map(
        workflow_ids: List[int],
    ) -> Dict[int, List[int]]:
        """Batch fetch change_workflow user IDs for workflows.

        Dedupes user IDs per workflow (same user may hold change from
        multiple sources) and returns sorted lists, matching
        ``get_users_with_change``.
        """
        ct = WorkflowPermissionService._get_content_type()

        rows = UserObjectPermission.objects.filter(
            permission__codename=WorkflowPermission.CHANGE,
            content_type=ct,
            object_pk__in=[str(wid) for wid in workflow_ids],
        ).values_list('object_pk', 'user_id')

        result: Dict[int, Set[int]] = defaultdict(set)
        for pk, uid in rows:
            result[int(pk)].add(uid)
        return {wid: sorted(uids) for wid, uids in result.items()}
