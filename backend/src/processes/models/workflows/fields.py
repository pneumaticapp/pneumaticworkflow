from django.contrib.auth import get_user_model
from django.db import models

from src.generics.managers import BaseSoftDeleteManager
from src.generics.models import SoftDeleteModel
from src.processes.models.mixins import (
    ApiNameMixin,
    FieldMixin,
)
from src.processes.models.workflows.kickoff import KickoffValue
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.workflow import Workflow
from src.processes.querysets import (
    FieldSelectionQuerySet,
    TaskFieldQuerySet,
)

UserModel = get_user_model()


class TaskField(
    SoftDeleteModel,
    FieldMixin,
    ApiNameMixin,
):

    class Meta:
        ordering = ['-order', 'id']

    value = models.TextField(
        blank=True,
        help_text='Human readable value',
    )
    clear_value = models.TextField(
        null=True,
        blank=True,
        help_text='Does not contains markdown',
    )
    markdown_value = models.TextField(
        null=True,
        blank=True,
        help_text='Contains markdown representation',
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='output',
        null=True,
    )
    user_id = models.IntegerField(null=True)
    group_id = models.IntegerField(null=True)
    kickoff = models.ForeignKey(
        KickoffValue,
        on_delete=models.CASCADE,
        related_name='output',
        null=True,
    )
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='fields',
    )
    objects = BaseSoftDeleteManager.from_queryset(TaskFieldQuerySet)()


class FieldSelection(
    SoftDeleteModel,
    ApiNameMixin,
):

    class Meta:
        ordering = ['pk']

    field = models.ForeignKey(
        TaskField,
        on_delete=models.CASCADE,
        related_name='selections',
    )
    is_selected = models.BooleanField(default=False)
    value = models.CharField(max_length=200)

    objects = BaseSoftDeleteManager.from_queryset(
        FieldSelectionQuerySet,
    )()
