from typing import List

from django.contrib.auth import get_user_model
from django.db import models
from guardian.shortcuts import assign_perm, get_objects_for_user

from src.generics.base.service import BaseModelService
from src.processes.enums import OwnerType
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.template import Template
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.workflow import Workflow
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment


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
                ).select_related('user')
                for template_owner in template_user_owners:
                    if template_owner.user:
                        users_set.add(template_owner.user)

        # Assign permissions to all collected users
        for user in users_set:
            assign_perm(
                'storage.view_file_attachment',
                user,
                self.instance,
            )

        # Assign permissions to groups
        for performer in task_performers:
            if performer.group:
                assign_perm(
                    'storage.view_file_attachment',
                    performer.group,
                    self.instance,
                )

    def _assign_template_permissions(self):
        """Assigns permissions for template."""
        template = self.instance.template
        if not template:
            return

        # Assign permissions to template owners
        template_owners = template.template_owners.all()
        for owner in template_owners:
            if owner.user:
                assign_perm(
                    'storage.view_file_attachment',
                    owner.user,
                    self.instance,
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
            ).select_related('user')
            for template_owner in template_user_owners:
                if template_owner.user:
                    users_set.add(template_owner.user)

        for user in users_set:
            assign_perm(
                'storage.view_file_attachment',
                user,
                self.instance,
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
        Creates attachments in bulk.
        Returns list of created attachments.
        """
        attachments = []
        for file_id in file_ids:
            attachment_data = {
                'file_id': file_id,
                'account': source.account,
                'access_type': AccessType.ACCOUNT,
            }

            # Determine source_type and relations
            if isinstance(source, Task):
                attachment_data.update({
                    'source_type': SourceType.TASK,
                    'task': source,
                })
            elif isinstance(source, Template):
                attachment_data.update({
                    'source_type': SourceType.TEMPLATE,
                    'template': source,
                })
            elif isinstance(source, Workflow):
                attachment_data.update({
                    'source_type': SourceType.WORKFLOW,
                    'workflow': source,
                })

            attachments.append(Attachment(**attachment_data))

        # Bulk create
        created_attachments = Attachment.objects.bulk_create(
            attachments,
            ignore_conflicts=True,
        )

        # Assign permissions for each created attachment
        for attachment in created_attachments:
            self.instance = attachment
            self._create_related()

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
                user_model = get_user_model()
                try:
                    user = user_model.objects.get(id=user_id)
                except user_model.DoesNotExist:
                    return False
            return user.has_perm(
                'storage.view_file_attachment',
                attachment,
            )

        return False

    def get_user_attachments(self, user):
        """
        Gets all attachments accessible to user.
        Uses django-guardian for filtering.
        """
        # Get attachments with permissions via guardian
        restricted_attachments = get_objects_for_user(
            user,
            'storage.view_file_attachment',
            klass=Attachment,
        ).filter(is_deleted=False)

        # Get account-level attachments
        account_attachments = Attachment.objects.filter(
            account=user.account,
            access_type=AccessType.ACCOUNT,
            is_deleted=False,
        )

        # Get public attachments
        public_attachments = Attachment.objects.filter(
            access_type=AccessType.PUBLIC,
            is_deleted=False,
        )

        # Combine querysets
        return (
            restricted_attachments |
            account_attachments |
            public_attachments
        ).distinct()
