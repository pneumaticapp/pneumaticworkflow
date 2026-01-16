import logging
from typing import List, Optional

import requests
from django.conf import settings

from src.processes.enums import FileAttachmentAccessType
from src.processes.models.workflows.attachment import FileAttachment
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService
from src.utils.salt import get_salt

logger = logging.getLogger(__name__)


class FileSyncService:
    """
    Service for synchronizing files between backend and file service.
    Creates records in the file service for existing files.
    """

    def __init__(self):
        self.file_service_url = settings.FILE_SERVICE_URL

    def sync_all_files(self) -> dict:
        """
        Synchronizes all files from FileAttachment with file service.
        Returns synchronization statistics.
        """
        stats = {
            'total': 0,
            'synced': 0,
            'skipped': 0,
            'errors': 0,
        }

        # Get all FileAttachment without file_id
        attachments = FileAttachment.objects.filter(
            file_id__isnull=True,
        ).select_related('account')

        stats['total'] = attachments.count()
        logger.info(
            "Starting sync for %s attachments",
            stats['total'],
        )

        for attachment in attachments:
            try:
                file_id = self.create_file_service_record(
                    attachment,
                )
                if file_id:
                    attachment.file_id = file_id
                    attachment.save(update_fields=['file_id'])
                    stats['synced'] += 1
                else:
                    stats['skipped'] += 1
            except (requests.RequestException, ValueError) as ex:
                logger.error(
                    "Error syncing attachment %s: %s",
                    attachment.id,
                    ex,
                )
                stats['errors'] += 1

        logger.info("Sync completed: %s", stats)
        return stats

    def sync_all_attachments_to_storage(self) -> dict:
        """
        Synchronizes FileAttachment records with storage.Attachment.
        Keeps legacy FileAttachment working while duplicating data.
        """
        stats = {
            'total': 0,
            'synced': 0,
            'skipped': 0,
            'errors': 0,
        }
        attachments = FileAttachment.objects.select_related(
            'account',
            'workflow',
            'event',
            'output',
        )
        stats['total'] = attachments.count()
        logger.info(
            "Starting storage sync for %s attachments",
            stats['total'],
        )
        for attachment in attachments:
            try:
                result = self.sync_single_attachment(
                    attachment=attachment,
                )
                if result:
                    stats['synced'] += 1
                else:
                    stats['skipped'] += 1
            except (requests.RequestException, ValueError) as ex:
                logger.error(
                    "Error syncing attachment %s: %s",
                    attachment.id,
                    ex,
                )
                stats['errors'] += 1
        logger.info("Storage sync completed: %s", stats)
        return stats

    def sync_single_attachment(
        self,
        attachment: FileAttachment,
        source_type: Optional[str] = None,
        task=None,
        workflow=None,
        template=None,
        access_type: Optional[str] = None,
    ) -> Optional[Attachment]:
        """
        Syncs a single FileAttachment to file service and storage.Attachment.
        Returns storage.Attachment or None on failure.
        """
        if not attachment:
            return None
        file_id = attachment.file_id
        if not file_id:
            file_id = self.create_file_service_record(attachment)
            if not file_id:
                return None
            attachment.file_id = file_id
            attachment.save(update_fields=['file_id'])
        if source_type is None:
            source_type = self._determine_source_type(attachment)
        if access_type is None:
            access_type = self._map_access_type(attachment, source_type)
        if task is None:
            task = self._get_task(attachment)
        if workflow is None:
            workflow = attachment.workflow or getattr(
                attachment.event,
                'workflow',
                None,
            )
        return self._upsert_storage_attachment(
            file_id=file_id,
            account=attachment.account,
            access_type=access_type,
            source_type=source_type,
            task=task,
            workflow=workflow,
            template=template,
        )

    def create_file_service_record(
        self,
        attachment: FileAttachment,
    ) -> Optional[str]:
        """
        Creates a record in the file service for an existing file.
        Returns file_id or None on error.
        """
        if not attachment.url:
            logger.warning(
                "Attachment %s has no URL",
                attachment.id,
            )
            return None

        # Generate file_id
        file_id = self._generate_file_id()

        # Prepare metadata for file service
        metadata = {
            'file_id': file_id,
            'account_id': attachment.account_id,
            'name': attachment.name,
            'url': attachment.url,
            'size': attachment.size,
            'thumbnail_url': attachment.thumbnail_url,
        }

        try:
            # Send metadata to file service
            response = requests.post(
                f'{self.file_service_url}/api/files/sync',
                json=metadata,
                timeout=30,
            )
            response.raise_for_status()
            return file_id
        except requests.RequestException as ex:
            logger.error(
                "Failed to create file service record: %s",
                ex,
            )
            return None

    def _generate_file_id(self) -> str:
        """Generates unique file_id."""
        return get_salt(32)

    def sync_to_new_attachment_model(
        self,
        file_attachments: List[FileAttachment],
    ) -> dict:
        """
        Synchronizes FileAttachment with new Attachment model.
        Used during data migration.
        """
        stats = {
            'total': len(file_attachments),
            'created': 0,
            'skipped': 0,
            'errors': 0,
        }

        for old_attachment in file_attachments:
            try:
                if not old_attachment.file_id:
                    stats['skipped'] += 1
                    continue

                # Determine source_type
                source_type = self._determine_source_type(
                    old_attachment,
                )

                # Create new attachment
                Attachment.objects.get_or_create(
                    file_id=old_attachment.file_id,
                    defaults={
                        'account': old_attachment.account,
                        'access_type': old_attachment.access_type,
                        'source_type': source_type,
                        'task': self._get_task(old_attachment),
                        'workflow': old_attachment.workflow,
                        'template': None,
                    },
                )
                stats['created'] += 1
            except (ValueError, AttributeError) as ex:
                logger.error(
                    "Error syncing attachment %s: %s",
                    old_attachment.id,
                    ex,
                )
                stats['errors'] += 1

        return stats

    def _determine_source_type(
        self,
        attachment: FileAttachment,
    ) -> str:
        """Determines source_type based on relations."""
        if attachment.workflow and not attachment.event:
            return SourceType.WORKFLOW
        if attachment.event and attachment.event.task:
            return SourceType.TASK
        if attachment.event and not attachment.event.task:
            return SourceType.WORKFLOW
        if attachment.output:
            return SourceType.TASK
        return SourceType.ACCOUNT

    def _map_access_type(
        self,
        attachment: FileAttachment,
        source_type: str,
    ) -> str:
        if attachment.access_type == FileAttachmentAccessType.RESTRICTED:
            return AccessType.RESTRICTED
        if source_type != SourceType.ACCOUNT:
            return AccessType.RESTRICTED
        return AccessType.ACCOUNT

    def _upsert_storage_attachment(
        self,
        file_id: str,
        account,
        access_type: str,
        source_type: str,
        task=None,
        workflow=None,
        template=None,
    ) -> Attachment:
        attachment, created = Attachment.objects.get_or_create(
            file_id=file_id,
            defaults={
                'account': account,
                'access_type': access_type,
                'source_type': source_type,
                'task': task,
                'workflow': workflow,
                'template': template,
            },
        )
        if not created:
            update_fields = []
            if attachment.account_id != account.id:
                attachment.account = account
                update_fields.append('account')
            if attachment.access_type != access_type:
                attachment.access_type = access_type
                update_fields.append('access_type')
            if attachment.source_type != source_type:
                attachment.source_type = source_type
                update_fields.append('source_type')
            if attachment.task_id != getattr(task, 'id', None):
                attachment.task = task
                update_fields.append('task')
            if attachment.workflow_id != getattr(workflow, 'id', None):
                attachment.workflow = workflow
                update_fields.append('workflow')
            if attachment.template_id != getattr(template, 'id', None):
                attachment.template = template
                update_fields.append('template')
            if update_fields:
                attachment.save(update_fields=update_fields)
        if attachment.access_type == AccessType.RESTRICTED:
            service = AttachmentService()
            service.instance = attachment
            service._create_related()
        return attachment

    def _get_task(
        self,
        attachment: FileAttachment,
    ):
        """Gets task from attachment."""
        if attachment.event and attachment.event.task:
            return attachment.event.task
        if attachment.output:
            return attachment.output.task
        return None
