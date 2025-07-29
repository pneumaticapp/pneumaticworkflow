from django.db import models
from django.db.models import UniqueConstraint, Q
from pneumatic_backend.processes.models.templates.task import TaskTemplate
from pneumatic_backend.processes.models.templates.template import Template
from pneumatic_backend.processes.models.base import BaseApiNameModel
from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.processes.querysets import (
    ChecklistTemplateQuerySet,
    ChecklistTemplateSelectionQuerySet
)


class ChecklistTemplate(
    BaseApiNameModel,
):

    class Meta:
        ordering = ('pk',)
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name'],
                condition=Q(is_deleted=False),
                name='processes_checklisttemplate_template_api_name_unique',
            )
        ]

    api_name_prefix = 'checklist'

    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='checklists',
    )
    task = models.ForeignKey(
        TaskTemplate,
        on_delete=models.CASCADE,
        related_name='checklists',
    )
    objects = BaseSoftDeleteManager.from_queryset(ChecklistTemplateQuerySet)()


class ChecklistTemplateSelection(
    BaseApiNameModel,
):

    class Meta:
        ordering = ('pk',)
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name'],
                condition=Q(is_deleted=False),
                name=(
                    'processes_checklisttemplateselection'
                    '_template_api_name_unique'
                ),
            ),
        ]

    api_name_prefix = 'cl-selection'

    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='checklist_selections',
    )
    checklist = models.ForeignKey(
        ChecklistTemplate,
        on_delete=models.CASCADE,
        related_name='selections'
    )
    value = models.CharField(max_length=2000)

    objects = BaseSoftDeleteManager.from_queryset(
        ChecklistTemplateSelectionQuerySet
    )()
