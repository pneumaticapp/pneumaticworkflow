from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVectorField
from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.generics.models import SoftDeleteModel
from pneumatic_backend.processes.models.mixins import (
    FieldMixin,
    ApiNameMixin,
)
from pneumatic_backend.processes.querysets import (
    FieldSelectionQuerySet,
    TaskFieldQuerySet,
)
from pneumatic_backend.processes.models.workflows.task import Task
from pneumatic_backend.processes.models.workflows.workflow import Workflow
from pneumatic_backend.processes.models.workflows.kickoff import KickoffValue


UserModel = get_user_model()


class TaskField(
    SoftDeleteModel,
    FieldMixin,
    ApiNameMixin
):

    class Meta:
        ordering = ['-order', 'id']

    value = models.TextField(
        blank=True,
        help_text='Human readable value'
    )
    clear_value = models.TextField(
        null=True,
        blank=True,
        help_text='Does not contains markdown'
    )
    markdown_value = models.TextField(
        null=True,
        blank=True,
        help_text='Contains markdown representation'
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
    search_content = SearchVectorField(null=True)
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
        related_name='selections'
    )
    is_selected = models.BooleanField(default=False)
    value = models.CharField(max_length=200)

    objects = BaseSoftDeleteManager.from_queryset(
        FieldSelectionQuerySet
    )()
