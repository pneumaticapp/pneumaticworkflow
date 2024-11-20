from django.db import models
from typing import Optional
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
from pneumatic_backend.processes.enums import FieldType
from pneumatic_backend.utils.dates import date_tsp_to_user_fmt

UserModel = get_user_model()


class TaskField(
    SoftDeleteModel,
    FieldMixin,
    ApiNameMixin
):

    class Meta:
        ordering = ['-order', 'id']

    value = models.TextField(blank=True)
    clear_value = models.TextField(
        null=True,
        blank=True,
        help_text='Does not contains markdown'
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='output',
        null=True,
    )
    # TODO deprecate template_id, use api_name
    template_id = models.IntegerField(null=True)
    user_id = models.IntegerField(null=True)
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

    def markdown_value(
        self,
        user: Optional[UserModel] = None
    ):
        if self.value:
            if self.type == FieldType.DATE:
                return date_tsp_to_user_fmt(
                    date_tsp=self.value,
                    user=user,
                )
            if self.type == FieldType.URL:
                return f'[{self.name}]({self.value})'
            elif self.type == FieldType.FILE:
                if self.value.find(',') > 0:
                    urls = [
                        f'[{self.name}]({url})'
                        for url in self.value.split(', ')
                    ]
                    return '\n'.join(urls)
                else:
                    return f'[{self.name}]({self.value})'
        return self.value


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
    # TODO deprecate template_id, use api_name
    template_id = models.IntegerField(
        null=True,
    )
    is_selected = models.BooleanField(default=False)
    value = models.CharField(max_length=200)

    objects = BaseSoftDeleteManager.from_queryset(
        FieldSelectionQuerySet
    )()
