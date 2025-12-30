from typing import List

from django.contrib.auth import get_user_model
from django.db import models
from guardian.shortcuts import assign_perm, get_objects_for_user

from src.generics.base.service import BaseModelService
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

        # Get task performers
        performers = task.performers.all()
        for performer in performers:
            if performer.user:
                assign_perm(
                    'storage.view_file_attachment',
                    performer.user,
                    self.instance,
                )
            elif performer.user_group:
                assign_perm(
                    'storage.view_file_attachment',
                    performer.user_group,
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

        # Assign permissions to workflow participants
        # Get all users from workflow tasks
        tasks = workflow.tasks.all()
        users_set = set()

        for task in tasks:
            performers = task.performers.all()
            for performer in performers:
                if performer.user:
                    users_set.add(performer.user)

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
            user_model = get_user_model()
            try:
                user = user_model.objects.get(id=user_id)
                return user.has_perm(
                    'storage.view_file_attachment',
                    attachment,
                )
            except user_model.DoesNotExist:
                return False

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
        )

        # Get account-level attachments
        account_attachments = Attachment.objects.filter(
            account=user.account,
            access_type=AccessType.ACCOUNT,
        )

        # Get public attachments
        public_attachments = Attachment.objects.filter(
            access_type=AccessType.PUBLIC,
        )

        # Combine querysets
        return (
            restricted_attachments |
            account_attachments |
            public_attachments
        ).distinct()
