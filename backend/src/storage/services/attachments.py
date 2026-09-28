from typing import Iterable, List, Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, models, transaction
from django.db.models import Q
from django.utils.functional import cached_property

from src.generics.base.service import BaseModelService
from src.permissions.models import (
    GroupObjectPermission,
    UserObjectPermission,
)
from src.permissions.enums import PermissionSource
from src.processes.enums import (
    DirectlyStatus,
    OwnerType,
    PerformerType,
    WorkflowPermission,
)
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.template import Template
from src.processes.models.workflows.task import Task, TaskPerformer
from src.processes.models.workflows.workflow import Workflow
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)

UserModel = get_user_model()


def clear_guardian_permissions_for_attachment_ids(
    attachment_ids: Iterable[int],
) -> None:
    """
    Remove guardian UserObjectPermission and GroupObjectPermission rows
    for the given Attachment ids. Generic object_pk links are not
    CASCADE-cleaned by Django; call before deleting attachments.
    """
    if not attachment_ids:
        return
    ctype = ContentType.objects.get_for_model(Attachment)
    obj_pks = [str(pk) for pk in attachment_ids]
    UserObjectPermission.objects.filter(
        content_type=ctype,
        object_pk__in=obj_pks,
    ).delete()
    GroupObjectPermission.objects.filter(
        content_type=ctype,
        object_pk__in=obj_pks,
    ).delete()


class AttachmentService(BaseModelService):
    """
    Service for working with attachments.
    Automatically assigns access permissions on creation.
    """

    @cached_property
    def _access_attachment_perm(self) -> Permission:
        ctype = ContentType.objects.get_for_model(Attachment)
        return Permission.objects.get(
            content_type=ctype,
            codename='access_attachment',
        )

    def _create_instance(self, **kwargs):
        """Creates Attachment instance."""
        self.instance = Attachment.objects.create(**kwargs)

    def _create_related(self, **kwargs):
        """
        Assigns permissions to attachment according to source_type
        and access_type.
        """
        if self.instance.access_type == AccessType.RESTRICTED:
            self._assign_restricted_permissions()

    def assign_permissions(self, attachment: Attachment) -> None:
        """Public API: assign permissions for a newly created attachment.

        Use this instead of calling _create_related() directly from
        external services (e.g., TaskFieldService).
        """
        self.instance = attachment
        self._create_related()

    def reassign_restricted_permissions(self, attachment: Attachment) -> None:
        """
        Re-assigns restricted permissions for existing attachment.
        Use when template/workflow participants change.
        """
        self.instance = attachment
        if attachment.access_type == AccessType.RESTRICTED:
            with transaction.atomic():
                self._assign_restricted_permissions()

    def _assign_restricted_permissions(self):
        """Assigns permissions for restricted access."""
        if self.instance.source_type == SourceType.TASK:
            self._assign_task_permissions()
        elif self.instance.source_type == SourceType.TEMPLATE:
            self._assign_template_permissions()
        elif self.instance.source_type == SourceType.WORKFLOW:
            self._assign_workflow_permissions()

    def assign_task_permissions_for_attachments(
        self,
        task: Task,
        attachments: Iterable[Attachment],
    ) -> None:
        """
        Additively grant task participants access to given attachments.

        Prefer ``rebuild_template_attachment_permissions`` for
        template-level files shared across workflows — additive
        grants cannot revoke access when a user leaves a workflow.
        """

        # Reload task to get latest performers
        task = Task.objects.prefetch_related(
            'taskperformer_set__user',
            'taskperformer_set__group',
        ).get(id=task.id)

        # (user, source_type, source_id) tuples
        user_sources = set()
        groups_set = set()

        # Collect task performers (single pass)
        task_performers = task.taskperformer_set.exclude_directly_deleted()
        for performer in task_performers:
            if performer.user:
                user_sources.add((
                    performer.user,
                    PermissionSource.PERFORMER,
                    performer.pk,
                ))
            if performer.group:
                groups_set.add(performer.group)

        # Collect workflow viewers from Guardian
        workflow = task.workflow
        wf_perm_service = WorkflowPermissionService(workflow)
        viewer_ids = wf_perm_service.get_users_with_view()
        if viewer_ids:
            for viewer in UserModel.objects.filter(id__in=viewer_ids):
                user_sources.add((
                    viewer,
                    PermissionSource.WORKFLOW_VIEWER,
                    workflow.pk,
                ))

        # Collect template owners (user + group)
        if workflow.template_id:
            template_owners = TemplateOwner.objects.filter(
                template_id=workflow.template_id,
                is_deleted=False,
            ).select_related('user', 'group')
            for to in template_owners:
                if to.type == OwnerType.USER and to.user:
                    user_sources.add((
                        to.user,
                        PermissionSource.TEMPLATE_OWNER,
                        to.pk,
                    ))
                elif to.type == OwnerType.GROUP and to.group:
                    groups_set.add(to.group)

        if not user_sources and not groups_set:
            return

        ctype = ContentType.objects.get_for_model(Attachment)
        perm = self._access_attachment_perm

        att_pks = [str(att.pk) for att in attachments]
        if not att_pks:
            return

        with transaction.atomic():
            # Bulk user permissions (1 query instead of NxM)
            if user_sources:
                user_perms = [
                    UserObjectPermission(
                        user=user,
                        permission=perm,
                        content_type=ctype,
                        object_pk=obj_pk,
                        source_type=st,
                        source_id=sid,
                    )
                    for user, st, sid in user_sources
                    for obj_pk in att_pks
                ]
                UserObjectPermission.objects.bulk_create(
                    user_perms,
                    ignore_conflicts=True,
                )

            # Bulk group permissions (1 query instead of GxM)
            if groups_set:
                group_perms = [
                    GroupObjectPermission(
                        group=group,
                        permission=perm,
                        content_type=ctype,
                        object_pk=obj_pk,
                    )
                    for group in groups_set
                    for obj_pk in att_pks
                ]
                GroupObjectPermission.objects.bulk_create(
                    group_perms,
                    ignore_conflicts=True,
                )

    def rebuild_template_attachment_permissions(
        self,
        template_id: int,
    ) -> None:
        """Full recalc of restricted TEMPLATE attachment ACL.

        Desired users:
          - template owners (USER)
          - any user with view_workflow on a live workflow
            of this template
        Desired groups:
          - template owners (GROUP)
          - active GROUP performers on tasks of those workflows

        Clear + rebuild (not additive) so users who lost all
        workflow access also lose template file access, while
        users still on another workflow of the same template keep it.
        """
        attachments = list(
            Attachment.objects.filter(
                template_id=template_id,
                source_type=SourceType.TEMPLATE,
                access_type=AccessType.RESTRICTED,
            ).only('id'),
        )
        if not attachments:
            return

        owner_user_sources = []
        owner_user_ids = set()
        owner_group_ids = set()
        template_owners = TemplateOwner.objects.filter(
            template_id=template_id,
            is_deleted=False,
        ).only('id', 'type', 'user_id', 'group_id')
        for owner in template_owners:
            if (
                owner.type == OwnerType.USER
                and owner.user_id is not None
            ):
                owner_user_ids.add(owner.user_id)
                owner_user_sources.append((
                    owner.user_id,
                    PermissionSource.TEMPLATE_OWNER,
                    owner.pk,
                ))
            elif (
                owner.type == OwnerType.GROUP
                and owner.group_id is not None
            ):
                owner_group_ids.add(owner.group_id)

        wf_ids = list(
            Workflow.objects.filter(
                template_id=template_id,
                is_deleted=False,
            ).values_list('id', flat=True),
        )

        viewer_ids = set()
        perf_group_ids = set()
        if wf_ids:
            wf_ct = ContentType.objects.get(
                app_label='processes',
                model='workflow',
            )
            viewer_ids = set(
                UserObjectPermission.objects.filter(
                    content_type=wf_ct,
                    permission__codename=WorkflowPermission.VIEW,
                    object_pk__in=[str(wid) for wid in wf_ids],
                ).values_list('user_id', flat=True),
            )
            perf_group_ids = set(
                TaskPerformer.objects.filter(
                    task__workflow_id__in=wf_ids,
                    type=PerformerType.GROUP,
                )
                .exclude(directly_status=DirectlyStatus.DELETED)
                .exclude(group_id__isnull=True)
                .values_list('group_id', flat=True),
            )

        derived_viewer_ids = viewer_ids - owner_user_ids
        desired_user_sources = list(owner_user_sources)
        for uid in derived_viewer_ids:
            desired_user_sources.append((
                uid,
                PermissionSource.WORKFLOW_VIEWER,
                template_id,
            ))
        desired_group_ids = owner_group_ids | perf_group_ids

        ctype = ContentType.objects.get_for_model(Attachment)
        perm = self._access_attachment_perm
        obj_pks = [str(att.pk) for att in attachments]

        with transaction.atomic():
            UserObjectPermission.objects.filter(
                content_type=ctype,
                object_pk__in=obj_pks,
            ).delete()
            GroupObjectPermission.objects.filter(
                content_type=ctype,
                object_pk__in=obj_pks,
            ).delete()

            if desired_user_sources:
                UserObjectPermission.objects.bulk_create(
                    [
                        UserObjectPermission(
                            user_id=uid,
                            permission=perm,
                            content_type=ctype,
                            object_pk=obj_pk,
                            source_type=st,
                            source_id=sid,
                        )
                        for uid, st, sid in desired_user_sources
                        for obj_pk in obj_pks
                    ],
                    ignore_conflicts=True,
                )

            if desired_group_ids:
                GroupObjectPermission.objects.bulk_create(
                    [
                        GroupObjectPermission(
                            group_id=gid,
                            permission=perm,
                            content_type=ctype,
                            object_pk=obj_pk,
                        )
                        for gid in desired_group_ids
                        for obj_pk in obj_pks
                    ],
                    ignore_conflicts=True,
                )

    def _assign_task_permissions(self):
        """Assigns permissions for task."""
        task = self.instance.task
        if not task:
            return

        # Reload task from DB to get latest performers and workflow data
        task = Task.objects.prefetch_related(
            'taskperformer_set__user',
            'taskperformer_set__group',
            'workflow__template',
        ).get(id=task.id)

        # Clear existing so removed performers lose access when we reassign
        ctype = ContentType.objects.get_for_model(Attachment)
        obj_pk = str(self.instance.pk)
        UserObjectPermission.objects.filter(
            content_type=ctype,
            object_pk=obj_pk,
        ).delete()
        GroupObjectPermission.objects.filter(
            content_type=ctype,
            object_pk=obj_pk,
        ).delete()

        perm = self._access_attachment_perm

        task_performers = task.taskperformer_set.exclude_directly_deleted()
        user_perms = []
        group_perms = []

        for performer in task_performers:
            if performer.user:
                user_perms.append(
                    UserObjectPermission(
                        user=performer.user,
                        permission=perm,
                        content_type=ctype,
                        object_pk=obj_pk,
                        source_type=PermissionSource.PERFORMER,
                        source_id=performer.pk,
                    ),
                )
            if performer.group:
                group_perms.append(
                    GroupObjectPermission(
                        group=performer.group,
                        permission=perm,
                        content_type=ctype,
                        object_pk=obj_pk,
                    ),
                )

        workflow = task.workflow
        if workflow:
            viewer_ids = WorkflowPermissionService(
                workflow,
            ).get_users_with_view()
            for uid in viewer_ids:
                user_perms.append(
                    UserObjectPermission(
                        user_id=uid,
                        permission=perm,
                        content_type=ctype,
                        object_pk=obj_pk,
                        source_type=PermissionSource.WORKFLOW_VIEWER,
                        source_id=workflow.pk,
                    ),
                )

            if workflow.template:
                template_user_owners = TemplateOwner.objects.filter(
                    template_id=workflow.template_id,
                    type=OwnerType.USER,
                    user__isnull=False,
                    is_deleted=False,
                )
                for to in template_user_owners:
                    user_perms.append(
                            UserObjectPermission(
                                user_id=to.user_id,
                                permission=perm,
                                content_type=ctype,
                                object_pk=obj_pk,
                                source_type=PermissionSource.TEMPLATE_OWNER,
                                source_id=to.pk,
                            ),
                    )

                template_group_owners = TemplateOwner.objects.filter(
                    template_id=workflow.template_id,
                    type=OwnerType.GROUP,
                    group__isnull=False,
                    is_deleted=False,
                )
                for to in template_group_owners:
                    group_perms.append(
                        GroupObjectPermission(
                            group_id=to.group_id,
                            permission=perm,
                            content_type=ctype,
                            object_pk=obj_pk,
                        ),
                    )

        if user_perms:
            UserObjectPermission.objects.bulk_create(
                user_perms, ignore_conflicts=True,
            )
        if group_perms:
            GroupObjectPermission.objects.bulk_create(
                group_perms, ignore_conflicts=True,
            )

    def _assign_template_permissions(self):
        """Assigns permissions for template."""
        template = self.instance.template
        if not template:
            return

        # Reload template to get current owners (after add/remove)
        template = Template.objects.prefetch_related('owners').get(
            pk=template.pk,
        )

        # Clear existing so removed owners lose access when we reassign
        ctype = ContentType.objects.get_for_model(Attachment)
        obj_pk = str(self.instance.pk)
        UserObjectPermission.objects.filter(
            content_type=ctype,
            object_pk=obj_pk,
        ).delete()
        GroupObjectPermission.objects.filter(
            content_type=ctype,
            object_pk=obj_pk,
        ).delete()

        perm = self._access_attachment_perm
        user_perms = []
        group_perms = []

        for owner in template.owners.filter(
            is_deleted=False,
        ):
            if owner.type == OwnerType.USER and owner.user_id:
                user_perms.append(
                    UserObjectPermission(
                        user_id=owner.user_id,
                        permission=perm,
                        content_type=ctype,
                        object_pk=obj_pk,
                        source_type=PermissionSource.TEMPLATE_OWNER,
                        source_id=owner.pk,
                    ),
                )
            elif owner.type == OwnerType.GROUP and owner.group_id:
                group_perms.append(
                    GroupObjectPermission(
                        group_id=owner.group_id,
                        permission=perm,
                        content_type=ctype,
                        object_pk=obj_pk,
                    ),
                )

        if user_perms:
            UserObjectPermission.objects.bulk_create(
                user_perms, ignore_conflicts=True,
            )
        if group_perms:
            GroupObjectPermission.objects.bulk_create(
                group_perms, ignore_conflicts=True,
            )

    def _assign_workflow_permissions(self):
        """Assigns permissions for workflow."""
        workflow = self.instance.workflow
        if not workflow and self.instance.event_id:
            workflow = getattr(
                self.instance.event, 'workflow', None,
            )
        if not workflow:
            return

        # Reload workflow from DB
        workflow = Workflow.objects.prefetch_related(
            'template',
        ).get(id=workflow.id)

        # Clear existing so removed participants lose access when we reassign
        ctype = ContentType.objects.get_for_model(Attachment)
        obj_pk = str(self.instance.pk)
        UserObjectPermission.objects.filter(
            content_type=ctype,
            object_pk=obj_pk,
        ).delete()
        GroupObjectPermission.objects.filter(
            content_type=ctype,
            object_pk=obj_pk,
        ).delete()

        perm = self._access_attachment_perm
        user_perms = []
        group_perms = []

        tasks = workflow.tasks.all()
        for task in tasks:
            performers = (
                task.taskperformer_set.exclude_directly_deleted()
            )
            for performer in performers:
                if performer.user_id:
                    user_perms.append(
                        UserObjectPermission(
                            user_id=performer.user_id,
                            permission=perm,
                            content_type=ctype,
                            object_pk=obj_pk,
                            source_type=PermissionSource.PERFORMER,
                            source_id=performer.pk,
                        ),
                    )
                if performer.group_id:
                    group_perms.append(
                        GroupObjectPermission(
                            group_id=performer.group_id,
                            permission=perm,
                            content_type=ctype,
                            object_pk=obj_pk,
                        ),
                    )

        viewer_ids = WorkflowPermissionService(
            workflow,
        ).get_users_with_view()
        for uid in viewer_ids:
            user_perms.append(
                UserObjectPermission(
                    user_id=uid,
                    permission=perm,
                    content_type=ctype,
                    object_pk=obj_pk,
                    source_type=PermissionSource.WORKFLOW_VIEWER,
                    source_id=workflow.pk,
                ),
            )

        if workflow.template:
            for to in TemplateOwner.objects.filter(
                template_id=workflow.template_id,
                is_deleted=False,
            ):
                if to.type == OwnerType.USER and to.user_id:
                    user_perms.append(
                        UserObjectPermission(
                            user_id=to.user_id,
                            permission=perm,
                            content_type=ctype,
                            object_pk=obj_pk,
                            source_type=PermissionSource.TEMPLATE_OWNER,
                            source_id=to.pk,
                        ),
                    )
                elif to.type == OwnerType.GROUP and to.group_id:
                    group_perms.append(
                        GroupObjectPermission(
                            group_id=to.group_id,
                            permission=perm,
                            content_type=ctype,
                            object_pk=obj_pk,
                        ),
                    )

        if user_perms:
            UserObjectPermission.objects.bulk_create(
                user_perms, ignore_conflicts=True,
            )
        if group_perms:
            GroupObjectPermission.objects.bulk_create(
                group_perms, ignore_conflicts=True,
            )

    def bulk_create(
        self,
        file_ids: List[str],
        source: models.Model,
    ) -> List[Attachment]:
        """
        Creates attachments one-by-one so each is persisted before
        assign_perm (django-guardian requires object with pk).
        Returns list of created attachments.
        """
        # Skip file_ids that already have a live attachment in this scope
        scope_filter = {'account': source.account}
        if isinstance(source, Task):
            scope_filter['task'] = source
        elif isinstance(source, Template):
            scope_filter['template'] = source
        elif isinstance(source, Workflow):
            scope_filter['workflow'] = source
        existing = set(
            Attachment.objects.filter(
                file_id__in=file_ids,
                **scope_filter,
            ).values_list('file_id', flat=True),
        )
        file_ids = [fid for fid in file_ids if fid not in existing]

        created_attachments = []
        for file_id in file_ids:
            attachment_data = {
                'file_id': file_id,
                'account': source.account,
            }

            if isinstance(source, Task):
                attachment_data.update(
                    {
                        'source_type': SourceType.TASK,
                        'task': source,
                        'access_type': AccessType.RESTRICTED,
                    },
                )
            elif isinstance(source, Template):
                attachment_data.update(
                    {
                        'source_type': SourceType.TEMPLATE,
                        'template': source,
                        'access_type': AccessType.RESTRICTED,
                    },
                )
            elif isinstance(source, Workflow):
                attachment_data.update(
                    {
                        'source_type': SourceType.WORKFLOW,
                        'workflow': source,
                        'access_type': AccessType.RESTRICTED,
                    },
                )
            else:
                attachment_data.update(
                    {
                        'access_type': AccessType.ACCOUNT,
                        'source_type': SourceType.ACCOUNT,
                    },
                )

            try:
                with transaction.atomic():
                    attachment = Attachment.objects.create(**attachment_data)
                    self.instance = attachment
                    self._create_related()
            except IntegrityError:
                continue
            created_attachments.append(attachment)

        return created_attachments

    def bulk_create_for_scope(
        self,
        file_ids: List[str],
        account,
        source_type: str,
        access_type: str = AccessType.RESTRICTED,
        task=None,
        workflow=None,
        template=None,
    ) -> List[Attachment]:
        """
        Create attachments one-by-one so each is persisted before
        assign_perm (django-guardian requires object with pk).
        """
        # Skip file_ids already present in this scope
        scope_filter = {'account': account}
        if task is not None:
            scope_filter['task'] = task
        elif workflow is not None:
            scope_filter['workflow'] = workflow
        elif template is not None:
            scope_filter['template'] = template
        existing = set(
            Attachment.objects.filter(
                file_id__in=file_ids,
                **scope_filter,
            ).values_list('file_id', flat=True),
        )
        file_ids = [fid for fid in file_ids if fid not in existing]

        created_attachments = []
        for file_id in file_ids:
            try:
                with transaction.atomic():
                    attachment = Attachment.objects.create(
                        file_id=file_id,
                        account=account,
                        access_type=access_type,
                        source_type=source_type,
                        task=task,
                        workflow=workflow,
                        template=template,
                    )
                    self.instance = attachment
                    self._create_related()
            except IntegrityError:
                continue
            created_attachments.append(attachment)
        return created_attachments

    def bulk_create_for_event(
        self,
        file_ids: List[str],
        account,
        source_type: str,
        event,
        access_type: str = AccessType.RESTRICTED,
    ) -> List[Attachment]:
        """
        Create attachments for WorkflowEvent one-by-one so each is persisted
        before assign_perm (django-guardian requires object with pk).
        """
        # Skip file_ids already attached to this event
        existing = set(
            Attachment.objects.filter(
                file_id__in=file_ids,
                event=event,
            ).values_list('file_id', flat=True),
        )
        file_ids = [fid for fid in file_ids if fid not in existing]

        created_attachments = []
        for file_id in file_ids:
            try:
                with transaction.atomic():
                    attachment = Attachment.objects.create(
                        file_id=file_id,
                        account=account,
                        access_type=access_type,
                        source_type=source_type,
                        event=event,
                        task=event.task if event.task_id else None,
                        workflow=event.workflow,
                    )
                    self.instance = attachment
                    self._create_related()
            except IntegrityError:
                continue
            created_attachments.append(attachment)
        return created_attachments

    def check_user_permission(
        self,
        user_id: Optional[int],
        account_id: Optional[int],
        file_id: str,
        public_template: Optional[Template] = None,
    ) -> bool:
        """
        Checks user permission to access file.

        A single file_id may have multiple Attachment records (one per
        scope).  Access is granted if ANY live attachment permits it.

        Optimized: all checks are pushed into SQL (no Python-side
        iteration over Attachment objects).
        """

        base_qs = Attachment.objects.filter(file_id=file_id)

        # Phase 1: single EXISTS — PUBLIC / ACCOUNT / public template
        fast_q = Q(access_type=AccessType.PUBLIC)
        if account_id is not None:
            fast_q |= Q(
                access_type=AccessType.ACCOUNT,
                account_id=account_id,
            )
        if public_template is not None:
            fast_q |= Q(
                access_type=AccessType.RESTRICTED,
                source_type=SourceType.TEMPLATE,
                template_id=public_template.id,
                account_id=public_template.account_id,
            )
        if base_qs.filter(fast_q).exists():
            return True

        # Phase 2: RESTRICTED — guardian object-level permissions
        if user_id is None:
            return False

        # Fetch only PKs of RESTRICTED attachments (no full objects)
        restricted_qs = base_qs.filter(
            access_type=AccessType.RESTRICTED,
        )
        if account_id is not None:
            restricted_qs = restricted_qs.filter(account_id=account_id)
        restricted_pks = list(restricted_qs.values_list('id', flat=True))
        if not restricted_pks:
            return False

        # Resolve user (deferred until actually needed)
        if hasattr(self, 'user') and self.user and self.user.id == user_id:
            user = self.user
        else:
            try:
                user = UserModel.objects.get(id=user_id)
            except UserModel.DoesNotExist:
                return False

        if not user.is_active:
            return False

        ctype = ContentType.objects.get_for_model(Attachment)
        perm_codename = 'access_attachment'
        str_pks = [str(pk) for pk in restricted_pks]

        if UserObjectPermission.objects.filter(
            user=user,
            object_pk__in=str_pks,
            permission__content_type=ctype,
            permission__codename=perm_codename,
        ).exists():
            return True

        user_group_ids = user.user_groups.values_list('id', flat=True)
        return GroupObjectPermission.objects.filter(
            group_id__in=user_group_ids,
            object_pk__in=str_pks,
            permission__content_type=ctype,
            permission__codename=perm_codename,
        ).exists()
