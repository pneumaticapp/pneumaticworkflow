from django.db import models
from django.db.models import UniqueConstraint, Q
from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.processes.models.mixins import FieldMixin
from pneumatic_backend.processes.querysets import (
    FieldTemplateValuesQuerySet,
    FieldTemplateQuerySet,
)
from pneumatic_backend.processes.models.templates.task import TaskTemplate
from pneumatic_backend.processes.models.templates.template import Template
from pneumatic_backend.processes.models.templates.kickoff import Kickoff
from pneumatic_backend.processes.models.base import BaseApiNameModel


class FieldTemplate(
    BaseApiNameModel,
    FieldMixin
):

    class Meta:
        ordering = ['-order']
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name'],
                condition=Q(is_deleted=False),
                name='processes_fieldtemplate_template_api_name_unique',
            )
        ]

    api_name_prefix = 'field'

    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='fields',
    )
    kickoff = models.ForeignKey(
        Kickoff,
        on_delete=models.CASCADE,
        null=True,
        related_name='fields'
    )
    task = models.ForeignKey(
        TaskTemplate,
        on_delete=models.CASCADE,
        null=True,
        related_name='fields'
    )
    date_created = models.DateTimeField(auto_now_add=True)
    default = models.TextField(blank=True)

    objects = BaseSoftDeleteManager.from_queryset(FieldTemplateQuerySet)()


class FieldTemplateSelection(
    BaseApiNameModel,
):

    class Meta:
        ordering = ['pk']
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name'],
                condition=Q(is_deleted=False),
                name=(
                    'processes_fieldtemplateselection'
                    '_template_api_name_unique'
                ),
            )
        ]

    api_name_prefix = 'selection'

    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='selections',
    )
    field_template = models.ForeignKey(
        FieldTemplate,
        on_delete=models.CASCADE,
        related_name='selections'
    )
    value = models.CharField(max_length=200)

    objects = BaseSoftDeleteManager.from_queryset(
        FieldTemplateValuesQuerySet
    )()
