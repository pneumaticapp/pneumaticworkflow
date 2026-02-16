from typing import List

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, models, transaction
from guardian.models import UserObjectPermission
from guardian.shortcuts import assign_perm, remove_perm

from src.generics.base.service import BaseModelService
from src.permissions.models import GroupObjectPermission
from src.processes.enums import OwnerType
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.template import Template
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.workflow import Workflow
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment

UserModel = get_user_model()


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
        elif self.instance.access_type == AccessType.ACCOUNT:
            self._assign_account_permissions()

    def reassign_restricted_permissions(self, attachment: Attachment) -> None:
        """
        Re-assigns restricted permissions for existing attachment.
        Use when template/workflow participants change.
        """
        self.instance = attachment
        if attachment.access_type == AccessType.RESTRICTED:
            self._assign_restricted_permissions()

    def _assign_restricted_permissions(self):
        """Assigns permissions for restricted access."""
        if self.instance.source_type == SourceType.TASK:
            self._assign_task_permissions()
        elif self.instance.source_type == SourceType.TEMPLATE:
            self._assign_template_permissions()
        elif self.instance.source_type == SourceType.WORKFLOW:
            self._assign_workflow_permissions()

    def _assign_task_permissions(self):
        """Assigns permissions for task."""
        task = self.instance.task
        if not task:
            return

        # Reload task from DB to get latest performers and workflow data
        task = Task.objects.prefetch_related(
            'taskperformer_set__user',
            'taskperformer_set__group',
            'workflow__owners',
            'workflow__members',
            'workflow__template',
        ).get(id=task.id)

        # Clear existing so removed performers lose access when we reassign
        for uop in UserObjectPermission.objects.filter(
                object_pk=str(self.instance.pk),
        ).select_related('user'):
            remove_perm(
                'storage.access_attachment',
                uop.user,
                self.instance,
            )
        ctype = ContentType.objects.get_for_model(Attachment)
        GroupObjectPermission.objects.filter(
            content_type=ctype,
            object_pk=str(self.instance.pk),
        ).delete()

        users_set = set()

        # Get task performers via intermediate model
        task_performers = task.taskperformer_set.all()
        for performer in task_performers:
            if performer.user:
                users_set.add(performer.user)

        # Get workflow owners and members
        workflow = task.workflow
        if workflow:
            workflow_owners = workflow.owners.all()
            for owner in workflow_owners:
                users_set.add(owner)

            workflow_members = workflow.members.all()
            for member in workflow_members:
                users_set.add(member)

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
        for uop in UserObjectPermission.objects.filter(
                object_pk=str(self.instance.pk),
        ).select_related('user'):
            remove_perm(
                'storage.access_attachment',
                uop.user,
                self.instance,
            )
        ctype = ContentType.objects.get_for_model(Attachment)
        GroupObjectPermission.objects.filter(
            content_type=ctype,
            object_pk=str(self.instance.pk),
        ).delete()

        # Assign permissions to template owners (exclude soft-deleted)
        template_owners = template.owners.filter(is_deleted=False)
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

        # Reload workflow from DB to get latest ManyToMany fields
        workflow = Workflow.objects.prefetch_related(
            'owners',
            'members',
            'template',
        ).get(id=workflow.id)

        # Clear existing so removed participants lose access when we reassign
        for uop in UserObjectPermission.objects.filter(
                object_pk=str(self.instance.pk),
        ).select_related('user'):
            remove_perm(
                'storage.access_attachment',
                uop.user,
                self.instance,
            )
        ctype = ContentType.objects.get_for_model(Attachment)
        GroupObjectPermission.objects.filter(
            content_type=ctype,
            object_pk=str(self.instance.pk),
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

        # Get owners from workflow (if assigned)
        workflow_owners = workflow.owners.all()
        for owner in workflow_owners:
            users_set.add(owner)

        workflow_members = workflow.members.all()
        for member in workflow_members:
            users_set.add(member)

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

    def _assign_account_permissions(self):
        """
        Assigns permissions for account access.
        All account users have access.
        """
        # For account access permissions are not assigned individually
        # Check will be done via account_id
        pass

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
        user_id: int,
        account_id: int,
        file_id: str,
    ) -> bool:
        """
        Checks user permission to access file.
        Uses django-guardian for object-level permission checks.
        """
        try:
            attachment = Attachment.objects.get(file_id=file_id)
        except Attachment.DoesNotExist:
            return False

        # Check access type
        if attachment.access_type == AccessType.PUBLIC:
            return True

        if attachment.access_type == AccessType.ACCOUNT:
            return account_id == attachment.account_id

        if attachment.access_type == AccessType.RESTRICTED:
            # Use django-guardian for permission check
            # Use self.user if available to avoid permission cache issues
            if hasattr(self, 'user') and self.user and self.user.id == user_id:
                user = self.user
            else:
                try:
                    user = UserModel.objects.get(id=user_id)
                except UserModel.DoesNotExist:
                    return False

            ctype = ContentType.objects.get_for_model(Attachment)
            perm_codename = 'access_attachment'
            obj_pk = str(attachment.pk)

            has_user_perm = UserObjectPermission.objects.filter(
                user=user,
                object_pk=obj_pk,
                permission__content_type=ctype,
                permission__codename=perm_codename,
            ).exists()

            if has_user_perm:
                return True

            user_group_ids = user.user_groups.values_list('id', flat=True)
            return GroupObjectPermission.objects.filter(
                group_id__in=user_group_ids,
                object_pk=obj_pk,
                permission__content_type=ctype,
                permission__codename=perm_codename,
            ).exists()

        return False
