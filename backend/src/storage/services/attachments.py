
from typing import Iterable, List, Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, models, transaction
from django.db.models import Q
from guardian.models import UserObjectPermission
from guardian.shortcuts import assign_perm

from src.generics.base.service import BaseModelService
from src.permissions.models import GroupObjectPermission
from src.processes.enums import OwnerType
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.template import Template
from src.processes.models.workflows.task import Task
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

        Unlike _assign_task_permissions (which clears + reassigns for a
        single task-level attachment), this method only ADDS permissions
        without removing existing ones. Used for template-level attachments
        that are shared across multiple workflows — clearing would revoke
        access granted by other workflows.

        Optimized: uses bulk_create(ignore_conflicts=True) to assign
        permissions in 2-3 queries instead of NxM individual calls.
        """

        # Reload task to get latest performers
        task = Task.objects.prefetch_related(
            'taskperformer_set__user',
            'taskperformer_set__group',
        ).get(id=task.id)

        users_set = set()
        groups_set = set()

        # Collect task performers (single pass)
        task_performers = task.taskperformer_set.exclude_directly_deleted()
        for performer in task_performers:
            if performer.user:
                users_set.add(performer.user)
            if performer.group:
                groups_set.add(performer.group)

        # Collect workflow viewers from Guardian
        workflow = task.workflow
        viewer_ids = WorkflowPermissionService.get_viewer_ids(workflow)
        if viewer_ids:
            users_set.update(
                UserModel.objects.filter(id__in=viewer_ids),
            )

        # Collect template owners (user + group)
        if workflow.template_id:
            template_owners = TemplateOwner.objects.filter(
                template_id=workflow.template_id,
                is_deleted=False,
            ).select_related('user', 'group')
            for to in template_owners:
                if to.type == OwnerType.USER and to.user:
                    users_set.add(to.user)
                elif to.type == OwnerType.GROUP and to.group:
                    groups_set.add(to.group)

        if not users_set and not groups_set:
            return

        ctype = ContentType.objects.get_for_model(Attachment)
        perm = Permission.objects.get(
            content_type=ctype,
            codename='access_attachment',
        )

        att_pks = [str(att.pk) for att in attachments]
        if not att_pks:
            return

        with transaction.atomic():
            # Bulk user permissions (1 query instead of NxM)
            if users_set:
                user_perms = [
                    UserObjectPermission(
                        user=user,
                        permission=perm,
                        content_type=ctype,
                        object_pk=obj_pk,
                    )
                    for user in users_set
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

        users_set = set()

        # Get task performers via intermediate model
        task_performers = task.taskperformer_set.exclude_directly_deleted()
        for performer in task_performers:
            if performer.user:
                users_set.add(performer.user)

        # Get workflow viewers from Guardian
        workflow = task.workflow
        if workflow:
            viewer_ids = WorkflowPermissionService.get_viewer_ids(workflow)
            if viewer_ids:
                users_set.update(
                    UserModel.objects.filter(id__in=viewer_ids),
                )

            # Get template owners
            if workflow.template:
                template_user_owners = TemplateOwner.objects.filter(
                    template_id=workflow.template_id,
                    type=OwnerType.USER,
                    user__isnull=False,
                    is_deleted=False,
                ).select_related('user')
                for template_owner in template_user_owners:
                    if template_owner.user:
                        users_set.add(template_owner.user)

        # Assign permissions to all collected users
        for user in users_set:
            assign_perm(
                'storage.access_attachment',
                user,
                self.instance,
            )

        # Assign permissions to groups (UserGroup; guardian.assign_perm
        # expects auth.Group, so we use GroupObjectPermission directly)
        perm = Permission.objects.get(
            content_type=ctype,
            codename='access_attachment',
        )
        for performer in task_performers:
            if performer.group:
                GroupObjectPermission.objects.get_or_create(
                    group=performer.group,
                    permission=perm,
                    content_type=ctype,
                    object_pk=str(self.instance.pk),
                )

        # Assign permissions to template owner groups
        if workflow and workflow.template:
            template_group_owners = TemplateOwner.objects.filter(
                template_id=workflow.template_id,
                type=OwnerType.GROUP,
                group__isnull=False,
                is_deleted=False,
            ).select_related('group')
            for template_owner in template_group_owners:
                if template_owner.group:
                    GroupObjectPermission.objects.get_or_create(
                        group=template_owner.group,
                        permission=perm,
                        content_type=ctype,
                        object_pk=str(self.instance.pk),
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

        # Assign permissions to template owners (exclude soft-deleted)
        template_owners = template.owners.filter(
            is_deleted=False,
            type=OwnerType.USER,
            user__isnull=False,
        )
        for owner in template_owners:
            if owner.user:
                assign_perm(
                    'storage.access_attachment',
                    owner.user,
                    self.instance,
                )

        # Assign permissions to template owner groups
        perm = Permission.objects.get(
            content_type=ctype,
            codename='access_attachment',
        )
        template_group_owners = template.owners.filter(
            is_deleted=False,
            type=OwnerType.GROUP,
            group__isnull=False,
        ).select_related('group')
        for owner in template_group_owners:
            if owner.group:
                GroupObjectPermission.objects.get_or_create(
                    group=owner.group,
                    permission=perm,
                    content_type=ctype,
                    object_pk=str(self.instance.pk),
                )

    def _assign_workflow_permissions(self):
        """Assigns permissions for workflow."""
        workflow = self.instance.workflow
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

        # Assign permissions to workflow participants
        users_set = set()

        # Get all users from workflow tasks
        tasks = workflow.tasks.all()
        for task in tasks:
            task_performers = task.taskperformer_set.all()
            for performer in task_performers:
                if performer.user:
                    users_set.add(performer.user)

        # Get viewers from Guardian (owners + members)
        viewer_ids = WorkflowPermissionService.get_viewer_ids(workflow)
        if viewer_ids:
            users_set.update(
                UserModel.objects.filter(id__in=viewer_ids),
            )

        # Also get owners from template (primary source)
        if workflow.template:
            # Get user owners directly from TemplateOwner
            template_user_owners = TemplateOwner.objects.filter(
                template_id=workflow.template_id,
                type=OwnerType.USER,
                user__isnull=False,
                is_deleted=False,
            ).select_related('user')
            for template_owner in template_user_owners:
                if template_owner.user:
                    users_set.add(template_owner.user)

        for user in users_set:
            assign_perm(
                'storage.access_attachment',
                user,
                self.instance,
            )

        # Assign permissions to groups from task performers and template owners
        perm = Permission.objects.get(
            content_type=ctype,
            codename='access_attachment',
        )
        # Get all task performer groups
        for task in tasks:
            task_performers = task.taskperformer_set.all()
            for performer in task_performers:
                if performer.group:
                    GroupObjectPermission.objects.get_or_create(
                        group=performer.group,
                        permission=perm,
                        content_type=ctype,
                        object_pk=str(self.instance.pk),
                    )

        # Get template owner groups
        if workflow.template:
            template_group_owners = TemplateOwner.objects.filter(
                template_id=workflow.template_id,
                type=OwnerType.GROUP,
                group__isnull=False,
                is_deleted=False,
            ).select_related('group')
            for template_owner in template_group_owners:
                if template_owner.group:
                    GroupObjectPermission.objects.get_or_create(
                        group=template_owner.group,
                        permission=perm,
                        content_type=ctype,
                        object_pk=str(self.instance.pk),
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
        restricted_pks = list(
            base_qs.filter(
                access_type=AccessType.RESTRICTED,
            ).values_list('id', flat=True),
        )
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
