from django.db import models

from src.accounts.models import AccountBaseMixin
from src.generics.managers import BaseSoftDeleteManager
from src.generics.models import SoftDeleteModel
from src.processes.querysets import AttachmentQuerySet
from src.storage.enums import AccessType, SourceType


class Attachment(SoftDeleteModel, AccountBaseMixin):
    """
    Model for storing file attachment information.
    Uses django-guardian for access permission management.
    """

    class Meta:
        permissions = (
            ('access_attachment', 'Can access attachment'),
        )
        indexes = [
            models.Index(fields=['file_id']),
            models.Index(fields=['source_type', 'account']),
            models.Index(
                fields=['is_deleted', 'access_type', 'account'],
                name='storage_att_del_acc_type_idx',
            ),
            models.Index(
                fields=['is_deleted', 'access_type'],
                name='storage_att_del_acc_idx',
            ),
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
    output = models.ForeignKey(
        'processes.TaskField',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='storage_attachments',
    )
    event = models.ForeignKey(
        'processes.WorkflowEvent',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='storage_attachments',
    )

    objects = BaseSoftDeleteManager.from_queryset(AttachmentQuerySet)()

    def delete(self, **kwargs):
        from src.storage.services.attachments import (  # noqa: PLC0415
            clear_guardian_permissions_for_attachment_ids,
        )
        clear_guardian_permissions_for_attachment_ids([self.pk])
        return super().delete(**kwargs)

    def __str__(self):
        return f"Attachment {self.file_id} ({self.source_type})"
