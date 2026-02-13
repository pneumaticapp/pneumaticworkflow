"""
Service for synchronizing files between backend and file service.
Creates records in the file service for existing files.
"""

import logging
from typing import Dict, List, Optional
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.contrib.auth import get_user_model

from src.processes.models.workflows.attachment import FileAttachment
from src.processes.models.workflows.task import Task
from src.storage.enums import SourceType
from src.storage.models import Attachment
from src.utils.salt import get_salt

UserModel = get_user_model()
logger = logging.getLogger(__name__)


class FileSyncService:
    """
    Service for synchronizing files between backend and file service.
    Creates records in the file service for existing files.
    """

    def __init__(self):
        """Initialize file sync service."""
        self.storage_url = getattr(
            settings, 'STORAGE_SERVICE_URL', 'http://localhost:8002',
        )

    def sync_all_files(self) -> Dict[str, int]:
        """
        Synchronize all FileAttachment records to file service.

        Returns:
            Dict with sync statistics: total, synced, skipped, errors.
        """
        stats = {'total': 0, 'synced': 0, 'skipped': 0, 'errors': 0}

        # Get all FileAttachment records without file_id
        file_attachments = FileAttachment.objects.filter(
            file_id__isnull=True,
        ).select_related('account')

        stats['total'] = file_attachments.count()

        for attachment in file_attachments:
            try:
                if self._should_skip_attachment(attachment):
                    stats['skipped'] += 1
                    continue

                file_id = self._generate_file_id(attachment)
                if file_id:
                    # Create record in file service
                    success = self._create_file_service_record(
                        attachment, file_id,
                    )
                    if success:
                        attachment.file_id = file_id
                        attachment.save(update_fields=['file_id'])
                        stats['synced'] += 1
                        logger.info(
                            'Synced attachment %s with file_id %s',
                            attachment.id, file_id,
                        )
                    else:
                        stats['errors'] += 1
                else:
                    stats['skipped'] += 1

            except (ValueError, AttributeError, TypeError) as e:
                logger.error(
                    'Error syncing attachment %s: %s',
                    attachment.id, str(e),
                )
                stats['errors'] += 1

        return stats

    def sync_all_attachments_to_storage(self) -> Dict[str, int]:
        """
        Synchronize all FileAttachment records to new Attachment model.

        Returns:
            Dict with sync statistics: total, synced, skipped, errors.
        """
        file_attachments = FileAttachment.objects.filter(
            file_id__isnull=False,
        ).select_related('account', 'workflow', 'event', 'output')
        return self.sync_to_new_attachment_model(list(file_attachments))

    def sync_to_new_attachment_model(
        self,
        attachments: List[FileAttachment],
    ) -> Dict[str, int]:
        """
        Synchronize given FileAttachment records to new Attachment model.

        Returns:
            Dict with sync statistics: total, created, skipped, errors.
        """
        stats = {'total': 0, 'created': 0, 'skipped': 0, 'errors': 0}
        stats['total'] = len(attachments)

        for attachment in attachments:
            try:
                if not attachment.file_id:
                    stats['skipped'] += 1
                    continue

                if Attachment.objects.filter(
                    file_id=attachment.file_id,
                ).exists():
                    stats['skipped'] += 1
                    continue

                source_type = self._determine_source_type(attachment)
                task = self._get_task(attachment)

                Attachment.objects.create(
                    file_id=attachment.file_id,
                    account_id=attachment.account_id,
                    source_type=source_type,
                    access_type=attachment.access_type,
                    task=task,
                    workflow=attachment.workflow,
                    template=None,
                    event=attachment.event,
                    output=attachment.output,
                )

                stats['created'] += 1
                logger.info(
                    'Created Attachment record for file_id %s',
                    attachment.file_id,
                )

            except (ValueError, AttributeError, TypeError) as e:
                logger.error(
                    'Error creating Attachment for file_id %s: %s',
                    attachment.file_id, str(e),
                )
                stats['errors'] += 1

        return stats

    def _should_skip_attachment(self, attachment: FileAttachment) -> bool:
        """Check if attachment should be skipped during sync."""
        # Skip if no URL or account
        if not attachment.url or not attachment.account:
            return True

        # Skip if URL doesn't look like a valid file URL
        return not self._is_valid_file_url(attachment.url)

    def _is_valid_file_url(self, url: str) -> bool:
        """Check if URL looks like a valid file URL."""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc and parsed.path)
        except (ValueError, AttributeError):
            return False

    def _generate_file_id(self, attachment: FileAttachment) -> Optional[str]:
        """Generate file_id from attachment URL."""
        try:
            # Extract filename from URL
            parsed_url = urlparse(attachment.url)
            filename = unquote(parsed_url.path.split('/')[-1])

            if not filename:
                return None

            # Generate unique file_id using salt
            salt = get_salt()
            file_id = (
                f"{attachment.account_id}_{attachment.id}_{salt}_{filename}"
            )

            return file_id[:64]  # Limit to 64 chars as per model

        except (ValueError, AttributeError, TypeError) as e:
            logger.error(
                'Error generating file_id for attachment %s: %s',
                attachment.id, str(e),
            )
            return None

    def _create_file_service_record(
        self,
        attachment: FileAttachment,
        file_id: str,
    ) -> bool:
        """Create record in file service for existing attachment."""
        try:
            # This would call the storage microservice to create a record
            # For now, just return True as placeholder
            # In real implementation, this would make HTTP call to storage
            # service

            payload = {
                'file_id': file_id,
                'filename': attachment.name,
                'size': attachment.size,
                'account_id': attachment.account_id,
                'url': attachment.url,
            }

            # Placeholder for actual HTTP call
            # response = requests.post(
            #     f"{self.storage_url}/sync",
            #     json=payload,
            #     timeout=30
            # )
            # return response.status_code == 201

            logger.info(
                'Would create file service record: %s', payload,
            )
            return True

        except (ValueError, AttributeError, TypeError) as e:
            logger.error(
                'Error creating file service record for %s: %s',
                file_id, str(e),
            )
            return False

    def _determine_source_type(self, attachment: FileAttachment) -> str:
        """Determine source type for Attachment model."""
        if attachment.workflow:
            return SourceType.WORKFLOW
        if attachment.event or attachment.output:
            return SourceType.TASK
        return SourceType.ACCOUNT

    def _get_task(self, attachment: FileAttachment) -> Optional[Task]:
        """Get task from attachment relationships."""
        if attachment.event and attachment.event.task:
            return attachment.event.task
        if attachment.output and attachment.output.task:
            return attachment.output.task
        return None
