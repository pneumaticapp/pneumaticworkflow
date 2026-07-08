import re
from typing import Iterable, Set, Tuple, TYPE_CHECKING, List, Dict
from collections import defaultdict

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q
from django.utils.functional import cached_property

from src.permissions.enums import PermissionSource
from src.permissions.models import UserObjectPermission
from src.processes.enums import (
    CommentStatus,
    DirectlyStatus,
    PerformerType,
    WorkflowEventType,
)

UserModel = get_user_model()

if TYPE_CHECKING:
    from src.processes.models.workflows.workflow import Workflow

# Matches: [John Doe| 123] -> captures "123"
MENTION_RE = re.compile(r'\[.*?\|\s*([0-9]+)\]')

CODENAME_VIEW = 'view_workflow'
CODENAME_CHANGE = 'change_workflow'


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

    # Type alias for source-aware entitled set (uid, type, id)
    _SourceTuple = Tuple[int, str, int]

    _ct_cache = None

    def __init__(self, workflow: 'Workflow'):
        self.workflow = workflow
        if WorkflowPermissionService._ct_cache is None:
            WorkflowPermissionService._ct_cache = (
                ContentType.objects.get_for_model(workflow)
            )
        self._ct = WorkflowPermissionService._ct_cache
        self._object_pk = str(workflow.pk)

    # ── Private helpers ───────────────────────────────────

    @cached_property
    def _view_perm(self):
        return Permission.objects.get(
            codename=CODENAME_VIEW,
            content_type=self._ct,
        )

    @cached_property
    def _change_perm(self):
        return Permission.objects.get(
            codename=CODENAME_CHANGE,
            content_type=self._ct,
        )

    # ── Write operations ──────────────────────────────────

    def grant_view(
        self,
        user: UserModel,
        source_type: str,
        source_id: int,
    ):
        """Grant view access to a single user, tagged with source.

        Replaces: workflow.members.add(user)
        """
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
        source_type: str,
        source_id: int,
    ):
        """Grant change + view access to a single user.

        Replaces: workflow.owners.add(user)
        Change implies view — owner can always see their workflow.
        """
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
        source_type: str,
        source_id: int,
    ):
        """Bulk-grant view access, tagged with source.

        Replaces: workflow.members.add(*user_ids)
        """
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

    def revoke_view_by_source(
        self,
        source_type: str,
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

    def sync_view_by_source(
        self,
        source_type: str,
        source_id: int,
        desired_user_ids: Iterable[int],
    ) -> Set[int]:
        """Diff-based sync of view permissions for a given source.

        Compares the current set of users who hold a view permission
        from (source_type, source_id) against ``desired_user_ids``:
        - users no longer desired are revoked,
        - users not yet present are granted,
        - users already present are left untouched.

        Returns:
            Set of user IDs that were actually granted.
            Callers can use this to send notifications only
            for truly new mentions.
        """
        desired = set(desired_user_ids)

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
    def set_owners(self, user_ids: Iterable[int]):
        """Replace all owners for a workflow.

        Replaces: workflow.owners.set(user_ids)
        Clears existing change perms, then assigns to the new set.
        Owners use source_type=TEMPLATE_OWNER since they derive from
        the template configuration.
        """
        change_perm = self._change_perm
        view_perm = self._view_perm

        UserObjectPermission.objects.filter(
            permission=change_perm,
            content_type=self._ct,
            object_pk=self._object_pk,
        ).delete()

        objs = []
        for uid in user_ids:
            for perm in (change_perm, view_perm):
                objs.append(UserObjectPermission(
                    user_id=uid,
                    permission=perm,
                    content_type=self._ct,
                    object_pk=self._object_pk,
                    source_type=PermissionSource.TEMPLATE_OWNER,
                    # 0 = workflow has no linked template (legacy data)
                    source_id=self.workflow.template_id or 0,
                ))
        if objs:
            # ignore_conflicts: skip if view row already exists from
            # another source (e.g. performer or mention)
            UserObjectPermission.objects.bulk_create(
                objs,
                ignore_conflicts=True,
            )

    @transaction.atomic
    def set_viewers(self):
        """Recalculate view_workflow permissions for a workflow.

        Collects all (user_id, source_type, source_id) tuples from
        active sources and performs a precise diff:
        - Removes UOP rows whose (user, source_type, source_id)
          no longer appears in the entitled set.
        - Adds UOP rows for new (user, source_type, source_id)
          combinations.

        This ensures each UOP row tracks exactly why it was
        granted and can be surgically revoked later.
        """
        view_perm = self._view_perm

        entitled = self._collect_entitled_sources()

        # All entitled user IDs (for the removal diff)
        entitled_user_ids = {uid for uid, _, _ in entitled}

        # Existing rows: (user_id, source_type, source_id)
        existing_rows = set(
            UserObjectPermission.objects.select_for_update().filter(
                permission=view_perm,
                content_type=self._ct,
                object_pk=self._object_pk,
            ).values_list('user_id', 'source_type', 'source_id'),
        )
        existing_user_ids = {uid for uid, _, _ in existing_rows}

        # 1. Remove all rows for users who lost ALL sources
        users_to_purge = existing_user_ids - entitled_user_ids
        if users_to_purge:
            UserObjectPermission.objects.filter(
                permission=view_perm,
                content_type=self._ct,
                object_pk=self._object_pk,
                user_id__in=users_to_purge,
            ).delete()

        # 2. For users who still have at least one source,
        #    remove individual rows whose source is no longer entitled.
        kept_existing = {
            row for row in existing_rows if row[0] not in users_to_purge
        }
        orphaned_source_rows = kept_existing - entitled
        if orphaned_source_rows:
            q_filter = Q()
            for uid, st, sid in orphaned_source_rows:
                q_filter |= Q(
                    user_id=uid,
                    source_type=st,
                    source_id=sid,
                )
            UserObjectPermission.objects.filter(
                q_filter,
                permission=view_perm,
                content_type=self._ct,
                object_pk=self._object_pk,
            ).delete()

        # 3. Add new source rows
        new_rows = entitled - existing_rows
        if new_rows:
            UserObjectPermission.objects.bulk_create(
                [
                    UserObjectPermission(
                        user_id=uid,
                        permission=view_perm,
                        content_type=self._ct,
                        object_pk=self._object_pk,
                        source_type=st,
                        source_id=sid,
                    )
                    for uid, st, sid in new_rows
                ],
                ignore_conflicts=True,
            )

    def _collect_entitled_sources(self) -> Set[_SourceTuple]:
        """Collect all (user_id, source_type, source_id) tuples.

        Each tuple represents one reason why a user should have
        view_workflow permission. Multiple tuples per user are
        normal (e.g. user is both a performer and mentioned).
        """
        from src.processes.models.workflows.task import TaskPerformer  # noqa: PLC0415

        entitled: Set[WorkflowPermissionService._SourceTuple] = set()
        workflow = self.workflow

        # 1. Template owners → source: TemplateOwner:<template_id>
        if workflow.template_id:
            from src.processes.models.templates.template import Template  # noqa: PLC0415
            owner_ids = Template.objects.filter(
                id=workflow.template_id,
            ).get_owners_as_users()
            for uid in owner_ids:
                entitled.add((
                    uid,
                    PermissionSource.TEMPLATE_OWNER,
                    workflow.template_id,
                ))

        # 2. Active task performers
        active_performers = (
            TaskPerformer.objects
            .filter(task__workflow=workflow)
            .exclude(directly_status=DirectlyStatus.DELETED)
            .exclude(task__is_deleted=True)
        )
        # 2a. Direct user performers → source: Performer:<task_id>
        for task_id, uid in (
            active_performers
            .filter(type=PerformerType.USER)
            .values_list('task_id', 'user_id')
        ):
            if uid is not None:
                entitled.add((
                    uid,
                    PermissionSource.PERFORMER,
                    task_id,
                ))

        # 2b. Group performer members → source: PerformerGroup:<group_id>
        from src.accounts.models import UserGroup  # noqa: PLC0415
        group_ids = list(
            active_performers
            .filter(type=PerformerType.GROUP)
            .values_list('group_id', flat=True),
        )
        if group_ids:
            group_members = (
                UserGroup.include_personal
                .filter(id__in=group_ids, is_deleted=False)
                .values_list('id', 'users__id')
            )
            for gid, uid in group_members:
                if uid is not None:
                    entitled.add((
                        uid,
                        PermissionSource.PERFORMER_GROUP,
                        gid,
                    ))

        # 3. Users mentioned in non-deleted comments
        #    → source: Mention:<workflow_event_id>
        entitled.update(
            self._get_mentioned_sources(workflow),
        )

        # 4. Users with change_workflow (managers always need view)
        #    Their view rows use the SAME source as their change rows
        for uid, st, sid in (
            UserObjectPermission.objects.filter(
                permission=self._change_perm,
                content_type=self._ct,
                object_pk=self._object_pk,
            ).values_list('user_id', 'source_type', 'source_id')
        ):
            entitled.add((uid, st, sid))

        # 5. Legacy migrated viewers -> source: WorkflowViewer:<workflow_id>
        for uid, st, sid in (
            UserObjectPermission.objects.filter(
                permission=self._view_perm,
                content_type=self._ct,
                object_pk=self._object_pk,
                source_type=PermissionSource.WORKFLOW_VIEWER,
            ).values_list('user_id', 'source_type', 'source_id')
        ):
            entitled.add((uid, st, sid))

        # 6. Vacation substitutes -> source: Vacation:<user_id>
        for uid, st, sid in (
            UserObjectPermission.objects.filter(
                permission=self._view_perm,
                content_type=self._ct,
                object_pk=self._object_pk,
                source_type=PermissionSource.VACATION,
            ).values_list('user_id', 'source_type', 'source_id')
        ):
            entitled.add((uid, st, sid))

        return entitled

    @staticmethod
    def _get_mentioned_sources(
        workflow: 'Workflow',
    ) -> Set['WorkflowPermissionService._SourceTuple']:
        """Extract (user_id, MENTION, event_id) tuples from comments."""
        from src.processes.models.workflows.event import WorkflowEvent  # noqa: PLC0415
        comments = (
            WorkflowEvent.objects
            .filter(
                workflow=workflow,
                type=WorkflowEventType.COMMENT,
                text__isnull=False,
            )
            .exclude(status=CommentStatus.DELETED)
            .values_list('id', 'text')
        )
        result: Set[WorkflowPermissionService._SourceTuple] = set()
        for event_id, text in comments:
            for uid_str in MENTION_RE.findall(text):
                result.add((
                    int(uid_str),
                    PermissionSource.MENTION,
                    event_id,
                ))
        return result

    # ── Read operations ───────────────────────────────────

    def has_view(self, user: UserModel) -> bool:
        """Check if user can view workflow.

        Uses direct UOP query instead of user.has_perm() because
        ObjectPermissionBackend's group check is incompatible with
        custom GroupObjectPermission model (UserGroup FK vs auth.Group).
        """
        return UserObjectPermission.objects.filter(
            user=user,
            permission__codename=CODENAME_VIEW,
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
            permission__codename=CODENAME_CHANGE,
            content_type=self._ct,
            object_pk=self._object_pk,
        ).exists()

    def get_viewer_ids(self) -> Set[int]:
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

    def get_owner_ids(self) -> List[int]:
        """Get sorted list of user IDs who can manage this workflow.

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
    def get_owners_map(workflow_ids: List[int]) -> Dict[int, List[int]]:
        """Batch fetch owner IDs for multiple workflows."""
        from src.processes.models.workflows.workflow import Workflow  # noqa: PLC0415

        ct = (
            WorkflowPermissionService._ct_cache or
            ContentType.objects.get_for_model(Workflow)
        )
        WorkflowPermissionService._ct_cache = ct

        rows = UserObjectPermission.objects.filter(
            permission__codename=CODENAME_CHANGE,
            content_type=ct,
            object_pk__in=[str(wid) for wid in workflow_ids],
        ).values_list('object_pk', 'user_id')

        result = defaultdict(list)
        for pk, uid in rows:
            result[int(pk)].append(uid)
        return result
