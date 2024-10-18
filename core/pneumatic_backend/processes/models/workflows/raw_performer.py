from django.db import models
from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.processes.models.mixins import RawPerformerMixin
from pneumatic_backend.processes.querysets import TaskPerformerQuerySet
from pneumatic_backend.processes.models.workflows.task import Task
from pneumatic_backend.processes.models.workflows.fields import TaskField
from pneumatic_backend.processes.models.workflows.workflow import Workflow
from pneumatic_backend.accounts.models import AccountBaseMixin
from pneumatic_backend.processes.models.base import BaseApiNameModel


class RawPerformer(
    BaseApiNameModel,
    AccountBaseMixin,
    RawPerformerMixin,
):

    api_name_prefix = 'raw-performer'

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='raw_performers',
    )
    task = models.ForeignKey(
        Task,
        related_name='raw_performers',
        on_delete=models.CASCADE
    )
    field = models.ForeignKey(
        TaskField,
        on_delete=models.CASCADE,
        related_name='raw_performers',
        null=True
    )
    # TODO deprecate template_id, use api_name
    template_id = models.IntegerField(null=True)
    task_performer_id = models.IntegerField(blank=True, null=True)

    objects = BaseSoftDeleteManager.from_queryset(TaskPerformerQuerySet)()
