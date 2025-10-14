from django.db import models

from src.accounts.models import AccountBaseMixin
from src.generics.managers import BaseSoftDeleteManager
from src.processes.models.base import BaseApiNameModel
from src.processes.models.mixins import RawPerformerMixin
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.workflow import Workflow
from src.processes.querysets import TaskPerformerQuerySet


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
        on_delete=models.CASCADE,
    )
    field = models.ForeignKey(
        TaskField,
        on_delete=models.CASCADE,
        related_name='raw_performers',
        null=True,
    )
    task_performer_id = models.IntegerField(blank=True, null=True)

    objects = BaseSoftDeleteManager.from_queryset(TaskPerformerQuerySet)()
