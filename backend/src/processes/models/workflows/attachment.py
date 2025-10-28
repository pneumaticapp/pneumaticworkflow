from typing import Optional
from urllib.parse import unquote

from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVectorField
from django.db import models

from src.accounts.models import AccountBaseMixin
from src.generics.managers import BaseSoftDeleteManager
from src.generics.models import SoftDeleteModel
from src.processes.enums import FileAttachmentAccessType
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.workflow import Workflow
from src.processes.querysets import FileAttachmentQuerySet

UserModel = get_user_model()


class FileAttachment(
    SoftDeleteModel,
    AccountBaseMixin,
):

    class Meta:
        ordering = ('id',)

    name = models.CharField(max_length=256)
    url = models.URLField(max_length=1024)
    thumbnail_url = models.URLField(max_length=1024, null=True, blank=True)
    size = models.PositiveIntegerField(default=0)
    file_id = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
    )
    event = models.ForeignKey(
        WorkflowEvent,
        on_delete=models.CASCADE,
        null=True,
        related_name='attachments',
    )
    output = models.ForeignKey(
        TaskField,
        on_delete=models.CASCADE,
        null=True,
        related_name='attachments',
    )
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='attachments',
        null=True,
    )
    access_type = models.CharField(
        max_length=20,
        choices=FileAttachmentAccessType.CHOICES,
        default=FileAttachmentAccessType.ACCOUNT,
    )
    search_content = SearchVectorField(null=True)

    objects = BaseSoftDeleteManager.from_queryset(FileAttachmentQuerySet)()

    @property
    def real_name(self):
        if not self.url:
            return None
        return self.url.split('/')[-1]

    @property
    def real_thumbnail_name(self):
        if not self.thumbnail_url:
            return None
        return self.thumbnail_url.split('/')[-1]

    @property
    def extension(self) -> Optional[str]:
        try:
            return unquote(self.url.split('/')[-1]).split('.')[-1]
        except IndexError:
            return None

    @property
    def humanize_size(self):
        size = float(self.size)
        for unit in ['B', 'KiB', 'MiB']:
            if abs(size) < 1024.0:
                return '%3.1f%s' % (size, unit)  # noqa: UP031
            size /= 1024.0
        return "%.1f%s" % (size, 'MiB')  # noqa: UP031


class FileAttachmentPermission(
    SoftDeleteModel,
    AccountBaseMixin,
):
    class Meta:
        unique_together = ('user', 'attachment')

    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='file_permissions',
    )
    attachment = models.ForeignKey(
        FileAttachment,
        on_delete=models.CASCADE,
        related_name='permissions',
    )
