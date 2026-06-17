from typing import Iterable, Set

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Subquery

from guardian.models import UserObjectPermission
from guardian.shortcuts import assign_perm, get_users_with_perms

UserModel = get_user_model()

PERM_VIEW = 'processes.view_workflow'
PERM_MANAGE = 'processes.manage_workflow'

# Raw SQL fragment: Guardian-based workflow owner join.
# Replaces: LEFT JOIN processes_workflow_owners
#   {alias} ON pw.id = {alias}.workflow_id
# The guardian_userobjectpermission table has
# `user_id` column just like the old M2M table,
# so WHERE clauses like `{alias}.user_id` work.
GUARDIAN_OWNER_JOIN_SQL = """
    LEFT JOIN guardian_userobjectpermission {alias} ON (
        {alias}.object_pk = CAST({workflow_col} AS VARCHAR)
        AND {alias}.content_type_id = (
            SELECT id FROM django_content_type
            WHERE app_label = 'processes' AND model = 'workflow'
        )
        AND {alias}.permission_id = (
            SELECT id FROM auth_permission
            WHERE codename = 'manage_workflow'
            AND content_type_id = (
                SELECT id FROM django_content_type
                WHERE app_label = 'processes' AND model = 'workflow'
            )
        )
    )
"""


class WorkflowPermissionService:
    """Unified permission management for Workflow objects.

    Replaces workflow.members and workflow.owners M2M fields
    with Guardian object-level permissions.

    Pattern mirrors AttachmentService from storage module.

    Permissions:
        view_workflow — read access (replaces members M2M)
        manage_workflow — lifecycle actions: terminate, return_to, finish
                         (replaces owners M2M)
    """

    # ── Write operations ──────────────────────────────────

    @classmethod
    def grant_view(cls, user, workflow) -> None:
        """Grant view access to a single user.

        Replaces: workflow.members.add(user)
        """
        assign_perm(PERM_VIEW, user, workflow)

    @classmethod
    def grant_manage(cls, user, workflow) -> None:
        """Grant manage + view access to a single user.

        Replaces: workflow.owners.add(user)
        Manage implies view — owner can always see their workflow.
        """
        assign_perm(PERM_VIEW, user, workflow)
        assign_perm(PERM_MANAGE, user, workflow)

    @classmethod
    def grant_view_bulk(cls, user_ids: Iterable[int], workflow) -> None:
        """Bulk-grant view access.

        Replaces: workflow.members.add(*user_ids)
        Uses bulk_create with ignore_conflicts (same pattern as storage).
        """
        if not user_ids:
            return
        ct = ContentType.objects.get_for_model(workflow)
        perm = Permission.objects.get(
            codename='view_workflow',
            content_type=ct,
        )
        UserObjectPermission.objects.bulk_create(
            [
                UserObjectPermission(
                    user_id=uid,
                    permission=perm,
                    content_type=ct,
                    object_pk=str(workflow.pk),
                )
                for uid in user_ids
            ],
            ignore_conflicts=True,
        )

    @classmethod
    def set_owners(cls, workflow, user_ids: Iterable[int]) -> None:
        """Replace all owners for a workflow.

        Replaces: workflow.owners.set(user_ids)
        Clears existing manage perms, then assigns to new set.
        """
        ct = ContentType.objects.get_for_model(workflow)
        manage_perm = Permission.objects.get(
            codename='manage_workflow',
            content_type=ct,
        )

        UserObjectPermission.objects.filter(
            permission=manage_perm,
            content_type=ct,
            object_pk=str(workflow.pk),
        ).delete()

        view_perm = Permission.objects.get(
            codename='view_workflow',
            content_type=ct,
        )

        objs = []
        for uid in user_ids:
            objs.append(UserObjectPermission(
                user_id=uid,
                permission=manage_perm,
                content_type=ct,
                object_pk=str(workflow.pk),
            ))
            objs.append(UserObjectPermission(
                user_id=uid,
                permission=view_perm,
                content_type=ct,
                object_pk=str(workflow.pk),
            ))
        if objs:
            UserObjectPermission.objects.bulk_create(
                objs,
                ignore_conflicts=True,
            )

    # ── Read operations ───────────────────────────────────

    @classmethod
    def has_view(cls, user, workflow) -> bool:
        """Check if user can view workflow.

        Uses direct UOP query instead of user.has_perm() because
        Guardian's group permission check is incompatible with
        custom UserGroup model (expects auth.Group).
        """
        return UserObjectPermission.objects.filter(
            user=user,
            permission__codename='view_workflow',
            content_type=ContentType.objects.get_for_model(workflow),
            object_pk=str(workflow.pk),
        ).exists()

    @classmethod
    def has_manage(cls, user, workflow) -> bool:
        """Check if user can manage workflow lifecycle.

        Uses direct UOP query instead of user.has_perm() because
        Guardian's group permission check is incompatible with
        custom UserGroup model (expects auth.Group).
        """
        return UserObjectPermission.objects.filter(
            user=user,
            permission__codename='manage_workflow',
            content_type=ContentType.objects.get_for_model(workflow),
            object_pk=str(workflow.pk),
        ).exists()

    @classmethod
    def get_viewer_ids(cls, workflow) -> Set[int]:
        """Get all user IDs who can view this workflow.

        Replaces: workflow.members.values_list('id', flat=True)
        Used for deduplication in mention notifications.
        """
        return set(
            get_users_with_perms(
                workflow,
                only_with_perms_in=['view_workflow'],
            ).values_list('id', flat=True),
        )

    @classmethod
    def get_owner_ids(cls, workflow) -> list:
        """Get sorted list of user IDs who can manage this workflow.

        Replaces: workflow.owners.values_list('id', flat=True)
        Used by API serializers to populate the 'owners' response field.
        """
        return list(
            get_users_with_perms(
                workflow,
                only_with_perms_in=['manage_workflow'],
            ).order_by('id').values_list('id', flat=True),
        )

    # ── QuerySet-level filters ────────────────────────────

    @classmethod
    def _get_perm_subquery(cls, user_id: int, codename: str) -> Subquery:
        """Return a Subquery of workflow PKs that user has permission for.

        Uses direct query on guardian_userobjectpermission table.
        """
        from src.processes.models.workflows.workflow import Workflow  # noqa: PLC0415
        ct = ContentType.objects.get_for_model(Workflow)
        return Subquery(
            UserObjectPermission.objects.filter(
                user_id=user_id,
                permission__codename=codename,
                content_type=ct,
            ).values('object_pk'),
        )

    @classmethod
    def viewer_q(cls, user_id: int, pk_field: str = 'pk') -> Q:
        """Return Q() filter for workflows user can view.

        Usage:
            Workflow.objects.filter(viewer_q(user.id))
            Workflow.objects.filter(viewer_q(user.id, pk_field='pk'))
            Task.objects.filter(viewer_q(user.id, pk_field='workflow_id'))
        """
        return Q(**{
            f'{pk_field}__in': cls._get_perm_subquery(
                user_id, 'view_workflow',
            ),
        })

    @classmethod
    def manager_q(cls, user_id: int, pk_field: str = 'pk') -> Q:
        """Return Q() filter for workflows user can manage."""
        return Q(**{
            f'{pk_field}__in': cls._get_perm_subquery(
                user_id, 'manage_workflow',
            ),
        })
