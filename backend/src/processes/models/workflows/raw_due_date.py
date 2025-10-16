from django.db import models

from src.generics.models import SoftDeleteModel
from src.processes.enums import DueDateRule
from src.processes.models.mixins import ApiNameMixin
from src.processes.models.workflows.task import Task


class RawDueDate(
    SoftDeleteModel,
    ApiNameMixin,
):

    class Meta:
        ordering = ('pk',)

    task = models.OneToOneField(
        Task,
        on_delete=models.CASCADE,
        related_name='raw_due_date',
    )
    duration = models.DurationField()
    duration_months = models.PositiveIntegerField(default=0)
    rule = models.CharField(
        choices=DueDateRule.CHOICES,
        max_length=100,
    )
    source_id = models.CharField(
        null=True,
        max_length=200,
    )
