import re
from typing import Iterable, Set, TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import IntegerField, Q, Subquery
from django.db.models.functions import Cast

from guardian.models import UserObjectPermission
from guardian.shortcuts import assign_perm, get_users_with_perms

from src.processes.enums import (
    CommentStatus,
    DirectlyStatus,
    PerformerType,
    WorkflowEventType,
)

UserModel = get_user_model()

if TYPE_CHECKING:
    from src.processes.models.workflows.workflow import Workflow

MENTION_RE = re.compile(r'\[.*?\|\s*([0-9]+)\]')

PERM_VIEW = 'processes.view_workflow'
PERM_CHANGE = 'processes.change_workflow'


class WorkflowPermissionService:
    """Unified permission management for Workflow objects.

    Replaces workflow.members and workflow.owners M2M fields
    with Guardian object-level permissions.

    Pattern mirrors AttachmentService from storage module.

    Permissions:
        view_workflow — read access (replaces members M2M)
        change_workflow — lifecycle actions + edit: resume, snooze,
                          finish, return_to, edit name/description
                          (replaces owners M2M)
    """

    # ── Write operations ──────────────────────────────────

    @classmethod
    def grant_view(cls, user: UserModel, workflow: 'Workflow') -> None:
        """Grant view access to a single user.

        Replaces: workflow.members.add(user)
        """
        assign_perm(PERM_VIEW, user, workflow)

    @classmethod
    def grant_manage(cls, user: UserModel, workflow: 'Workflow') -> None:
        """Grant change + view access to a single user.

        Replaces: workflow.owners.add(user)
        Change implies view — owner can always see their workflow.
        """
        assign_perm(PERM_VIEW, user, workflow)
        assign_perm(PERM_CHANGE, user, workflow)

    @classmethod
    def grant_view_bulk(
        cls,
        user_ids: Iterable[int],
        workflow: 'Workflow',
    ) -> None:
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
    def set_owners(cls, workflow: 'Workflow', user_ids: Iterable[int]) -> None:
        """Replace all owners for a workflow.

        Replaces: workflow.owners.set(user_ids)
        Clears existing manage perms, then assigns to new set.
        """
        ct = ContentType.objects.get_for_model(workflow)
        manage_perm = Permission.objects.get(
            codename='change_workflow',
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

    @classmethod
    def set_viewers(cls, workflow: 'Workflow') -> None:
        """Recalculate view_workflow permissions for a workflow.

        Collects all user IDs who SHOULD have view access from:
        1. Template owners (always have view via manage)
        2. Active task performers (direct users + group members)
        3. Users mentioned in non-deleted comments

        Removes view_workflow for users not in this set.
        Adds view_workflow for users who should have it.
        """
        from src.processes.models.workflows.task import TaskPerformer  # noqa: PLC0415

        entitled_ids = set()

        # 1. Template owners (they have manage → always need view)
        if workflow.template_id:
            from src.processes.models.templates.template import Template  # noqa: PLC0415
            entitled_ids.update(
                Template.objects.filter(
                    id=workflow.template_id,
                ).get_owners_as_users(),
            )

        # 2. Active task performers (user + group members)
        active_performers = (
            TaskPerformer.objects
            .filter(
                task__workflow=workflow,
                task__is_deleted=False,
            )
            .exclude(
                directly_status=DirectlyStatus.DELETED,
            )
        )
        # Direct user performers
        entitled_ids.update(
            active_performers
            .filter(type=PerformerType.USER, user_id__isnull=False)
            .values_list('user_id', flat=True),
        )
        # Group performer members
        from src.accounts.models import UserGroup  # noqa: PLC0415
        group_ids = list(
            active_performers
            .filter(type=PerformerType.GROUP, group_id__isnull=False)
            .values_list('group_id', flat=True),
        )
        if group_ids:
            entitled_ids.update(
                UserGroup.objects
                .filter(id__in=group_ids, is_deleted=False)
                .values_list('users__id', flat=True),
            )

        # 3. Users mentioned in non-deleted comments
        entitled_ids.update(
            cls._get_mentioned_user_ids(workflow),
        )

        # Discard None (from empty group memberships etc.)
        entitled_ids.discard(None)

        ct = ContentType.objects.get_for_model(workflow)
        view_perm = Permission.objects.get(
            codename='view_workflow',
            content_type=ct,
        )
        object_pk = str(workflow.pk)

        # Remove view from users who lost all access sources
        UserObjectPermission.objects.filter(
            permission=view_perm,
            content_type=ct,
            object_pk=object_pk,
        ).exclude(
            user_id__in=entitled_ids,
        ).delete()

        # Add view for users who should have it but don't yet
        existing_ids = set(
            UserObjectPermission.objects.filter(
                permission=view_perm,
                content_type=ct,
                object_pk=object_pk,
            ).values_list('user_id', flat=True),
        )
        new_ids = entitled_ids - existing_ids
        if new_ids:
            UserObjectPermission.objects.bulk_create(
                [
                    UserObjectPermission(
                        user_id=uid,
                        permission=view_perm,
                        content_type=ct,
                        object_pk=object_pk,
                    )
                    for uid in new_ids
                ],
                ignore_conflicts=True,
            )

    @classmethod
    def _get_mentioned_user_ids(cls, workflow: 'Workflow') -> Set[int]:
        """Extract user IDs mentioned in non-deleted comments.

        Mention format: [Display Name| 123]
        """
        from src.processes.models.workflows.event import WorkflowEvent  # noqa: PLC0415
        comments = (
            WorkflowEvent.objects
            .filter(
                workflow=workflow,
                type=WorkflowEventType.COMMENT,
                text__isnull=False,
            )
            .exclude(status=CommentStatus.DELETED)
            .values_list('text', flat=True)
        )
        mentioned_ids = set()
        for text in comments:
            ids = MENTION_RE.findall(text)
            mentioned_ids.update(int(uid) for uid in ids)
        return mentioned_ids

    # ── Read operations ───────────────────────────────────

    @classmethod
    def has_view(cls, user: UserModel, workflow: 'Workflow') -> bool:
        """Check if user can view workflow.

        Uses direct UOP query instead of user.has_perm() because
        ObjectPermissionBackend's group check is incompatible with
        custom GroupObjectPermission model (UserGroup FK vs auth.Group).
        """
        return UserObjectPermission.objects.filter(
            user=user,
            permission__codename='view_workflow',
            content_type=ContentType.objects.get_for_model(workflow),
            object_pk=str(workflow.pk),
        ).exists()

    @classmethod
    def has_manage(cls, user: UserModel, workflow: 'Workflow') -> bool:
        """Check if user can manage workflow lifecycle.

        Uses direct UOP query instead of user.has_perm() because
        ObjectPermissionBackend's group check is incompatible with
        custom GroupObjectPermission model (UserGroup FK vs auth.Group).
        """
        return UserObjectPermission.objects.filter(
            user=user,
            permission__codename='change_workflow',
            content_type=ContentType.objects.get_for_model(workflow),
            object_pk=str(workflow.pk),
        ).exists()

    @classmethod
    def get_viewer_ids(cls, workflow: 'Workflow') -> Set[int]:
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
    def get_owner_ids(cls, workflow: 'Workflow') -> list:
        """Get sorted list of user IDs who can manage this workflow.

        Replaces: workflow.owners.values_list('id', flat=True)
        Used by API serializers to populate the 'owners' response field.
        """
        return list(
            get_users_with_perms(
                workflow,
                only_with_perms_in=['change_workflow'],
            ).order_by('id').values_list('id', flat=True),
        )

    # ── QuerySet-level filters ────────────────────────────

    @classmethod
    def _get_perm_subquery(cls, user_id: int, codename: str) -> Subquery:
        """Return a Subquery of workflow PKs that user has permission for.

        Uses direct query on guardian_userobjectpermission table.
        Cast object_pk (varchar) to integer so PostgreSQL can
        compare with workflow.id without type mismatch.
        """
        from src.processes.models.workflows.workflow import (  # noqa: PLC0415
            Workflow,
        )
        ct = ContentType.objects.get_for_model(Workflow)
        return Subquery(
            UserObjectPermission.objects.filter(
                user_id=user_id,
                permission__codename=codename,
                content_type=ct,
            ).annotate(
                object_pk_int=Cast('object_pk', IntegerField()),
            ).values('object_pk_int'),
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
                user_id, 'change_workflow',
            ),
        })
