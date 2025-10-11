from django.db import models
from src.processes.models.mixins import ApiNameMixin
from src.generics.models import SoftDeleteModel
from src.generics.managers import BaseSoftDeleteManager
from src.processes.models.workflows.task import Task
from src.processes.querysets import (
    ChecklistQuerySet,
    ChecklistSelectionQuerySet,
)


class Checklist(
    SoftDeleteModel,
    ApiNameMixin,
):

    class Meta:
        ordering = ('pk',)

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='checklists',
    )
    objects = BaseSoftDeleteManager.from_queryset(ChecklistQuerySet)()


class ChecklistSelection(
    SoftDeleteModel,
    ApiNameMixin,
):

    class Meta:
        ordering = ('pk',)

    checklist = models.ForeignKey(
        Checklist,
        on_delete=models.CASCADE,
        related_name='selections',
    )
    date_selected = models.DateTimeField(
        null=True,
        verbose_name='The date the selection was marked',
    )
    selected_user_id = models.IntegerField(
        null=True,
        verbose_name='The user who mark or unmark selection',
    )
    value = models.TextField()
    value_template = models.TextField()

    objects = BaseSoftDeleteManager.from_queryset(
        ChecklistSelectionQuerySet,
    )()

    @property
    def is_selected(self):
        return self.date_selected is not None
