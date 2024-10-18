from django.db import models
from django.db.models import UniqueConstraint, Q
from pneumatic_backend.processes.models.base import BaseApiNameModel
from pneumatic_backend.processes.models import (
    Template,
    TaskTemplate
)
from pneumatic_backend.processes.enums import DueDateRule


class RawDueDateTemplate(
    BaseApiNameModel,
):

    class Meta:
        ordering = ('pk',)
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name'],
                condition=Q(is_deleted=False),
                name='processes_rawduedatetemplate_template_api_name_unique',
            )
        ]

    api_name_prefix = 'raw-due-date'
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='raw_due_dates',
    )
    task = models.OneToOneField(
        TaskTemplate,
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
