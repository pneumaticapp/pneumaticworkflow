from django.db import models
from pneumatic_backend.processes.models.mixins import ApiNameMixin
from pneumatic_backend.generics.models import SoftDeleteModel
from pneumatic_backend.processes.enums import DueDateRule
from pneumatic_backend.processes.models import Task


class RawDueDate(
    SoftDeleteModel,
    ApiNameMixin,
):

    class Meta:
        ordering = ('pk',)

    task = models.OneToOneField(
        Task,
        on_delete=models.CASCADE,
        related_name='raw_due_date'
    )
    duration = models.DurationField()
    duration_months = models.PositiveIntegerField(default=0)
    rule = models.CharField(
        choices=DueDateRule.CHOICES,
        max_length=100
    )
    source_id = models.CharField(
        null=True,
        max_length=200
    )
