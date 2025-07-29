from typing import Optional
from urllib.parse import unquote
from django.db import models
from django.contrib.postgres.search import SearchVectorField
from pneumatic_backend.accounts.models import AccountBaseMixin
from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.generics.models import SoftDeleteModel
from pneumatic_backend.processes.querysets import FileAttachmentQuerySet
from pneumatic_backend.processes.models.workflows.fields import TaskField
from pneumatic_backend.processes.models.workflows.workflow import Workflow
from pneumatic_backend.processes.models.workflows.event import WorkflowEvent


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
    event = models.ForeignKey(
        WorkflowEvent,
        on_delete=models.CASCADE,
        null=True,
        related_name='attachments'
    )
    output = models.ForeignKey(
        TaskField,
        on_delete=models.CASCADE,
        null=True,
        related_name='attachments'
    )
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='attachments',
        null=True,
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
                return '%3.1f%s' % (size, unit)
            size /= 1024.0
        return "%.1f%s" % (size, 'MiB')
