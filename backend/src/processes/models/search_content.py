from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.db.models import Q, UniqueConstraint

from src.accounts.models import AccountBaseMixin
from src.generics.models import SoftDeleteModel
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.templates.template import Template
from src.processes.models.workflows.workflow import Workflow
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.event import WorkflowEvent


class SearchContent(
    SoftDeleteModel,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['id']
        constraints = [
            UniqueConstraint(
                fields=[
                    'workflow',
                    'task',
                    'event',
                    'task_field',
                    'template',
                    'task_template',
                ],
                condition=Q(is_deleted=False),
                name='processes_search_content_unique',
            ),
        ]

    content = SearchVectorField(null=True, blank=True)
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        null=True,
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        null=True,
    )
    event = models.ForeignKey(
        WorkflowEvent,
        on_delete=models.CASCADE,
        null=True,
    )
    task_field = models.ForeignKey(
        TaskField,
        on_delete=models.CASCADE,
        null=True,
    )
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        null=True,
    )
    task_template = models.ForeignKey(
        TaskTemplate,
        on_delete=models.CASCADE,
        null=True,
    )

    def __str__(self):
        return str(self.content)
