from django.db import models

from src.accounts.models import AccountBaseMixin
from src.generics.models import SoftDeleteModel
from src.storage.enums import AccessType, SourceType


class Attachment(SoftDeleteModel, AccountBaseMixin):
    """
    Model for storing file attachment information.
    Uses django-guardian for access permission management.
    """

    class Meta:
        permissions = (
            ('view_file_attachment', 'Can view file attachment'),
        )
        indexes = [
            models.Index(fields=['file_id']),
            models.Index(fields=['source_type', 'account']),
        ]

    file_id = models.CharField(
        max_length=64,
        unique=True,
        help_text='Unique file identifier in the file service',
    )
    access_type = models.CharField(
        max_length=20,
        choices=AccessType.CHOICES,
        default=AccessType.ACCOUNT,
        help_text='File access type',
    )
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.CHOICES,
        help_text='File source type',
    )

    # Relations to sources
    template = models.ForeignKey(
        'processes.Template',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='storage_attachments',
    )
    task = models.ForeignKey(
        'processes.Task',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='storage_attachments',
    )
    workflow = models.ForeignKey(
        'processes.Workflow',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='storage_attachments',
    )

    def __str__(self):
        return f"Attachment {self.file_id} ({self.source_type})"
