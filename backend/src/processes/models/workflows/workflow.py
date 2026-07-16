# ruff: noqa: PLC0415
from typing import Dict, Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.utils import timezone

from src.accounts.models import AccountBaseMixin
from src.generics.managers import BaseSoftDeleteManager
from src.generics.models import SoftDeleteModel
from src.processes.enums import WorkflowStatus
from src.processes.models.mixins import WorkflowMixin
from src.processes.models.templates.template import Template
from src.processes.querysets import (
    TaskFieldQuerySet,
    WorkflowQuerySet,
)
from src.processes.utils.common import get_workflow_starter_name

UserModel = get_user_model()


class Workflow(
    SoftDeleteModel,
    AccountBaseMixin,
    WorkflowMixin,
):

    class Meta:
        ordering = ['-date_created']

    name = models.TextField()
    name_template = models.TextField(null=True, blank=True)
    legacy_template_name = models.TextField(null=True, blank=True)
    template = models.ForeignKey(
        Template,
        on_delete=models.SET_NULL,
        related_name='workflows',
        null=True,
    )
    status = models.IntegerField(
        choices=WorkflowStatus.CHOICES,
        default=WorkflowStatus.RUNNING,
    )
    status_updated = models.DateTimeField(db_index=True)
    is_external = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)
    is_legacy_template = models.BooleanField(
        help_text='Template is deleted',
        default=False,
    )
    members = models.ManyToManyField(
        UserModel,
        related_name='workflows',
    )
    owners = models.ManyToManyField(
        UserModel,
        related_name='owners',
        verbose_name='owners',
    )
    workflow_starter = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        related_name='started_workflow',
        null=True,
    )
    date_completed = models.DateTimeField(null=True)
    due_date = models.DateTimeField(null=True)
    ancestor_task = models.ForeignKey(
        'Task',
        null=True,
        help_text='The task within which the subprocess should be executed',
        on_delete=models.SET_NULL,
        related_name='sub_workflows',
    )

    objects = BaseSoftDeleteManager.from_queryset(WorkflowQuerySet)()

    def webhook_payload(self):
        from src.processes.serializers.workflows.workflow import (
            WorkflowDetailsSerializer,
        )
        return {
            'workflow': WorkflowDetailsSerializer(instance=self).data,
        }

    def __str__(self):
        return f'(Workflow {self.id}) {self.name}'

    def is_version_lower(self, version):
        return version > self.version

    def save(self, update_fields=None, **kwargs):
        if update_fields is not None and 'status' in update_fields:
            self.status_updated = timezone.now()
            update_fields.append('status_updated')
        super().save(update_fields=update_fields, **kwargs)

    def _get_kickoff(self):
        kickoff = self.kickoff.prefetch_related('output__selections').first()
        if not kickoff:
            from src.processes.models.workflows\
                .kickoff import KickoffValue
            kickoff = KickoffValue(
                workflow=self,
                account_id=self.account_id,
            )
        return kickoff

    def _get_task(self, number, tasks):
        for task in tasks:
            if task.number == number:
                return task
        from src.processes.models.workflows \
            .task import Task
        return Task(
            workflow=self,
            number=number,
        )

    def get_kickoff_output_fields(
        self,
        fields_filter_kwargs: Optional[Dict] = None,
    ) -> TaskFieldQuerySet:

        """ Return the output fields from kickoff """

        from src.processes.models.workflows.fields import TaskField
        kickoff = self.kickoff.get()
        qst = TaskField.objects.filter(
            Q(
                Q(kickoff_id=kickoff.id) |
                Q(fieldset__kickoff_id=kickoff.id),
            ),
        )
        if fields_filter_kwargs:
            qst = qst.filter(**fields_filter_kwargs)
        return qst

    def get_tasks_output_fields(
        self,
        tasks_filter_kwargs: Optional[Dict] = None,
        tasks_exclude_kwargs: Optional[Dict] = None,
        fields_filter_kwargs: Optional[Dict] = None,
    ) -> TaskFieldQuerySet:

        """ Return the output fields from tasks """

        from src.processes.models.workflows.fields import TaskField

        tasks_filter_kwargs = tasks_filter_kwargs or {}
        tasks_exclude_kwargs = tasks_exclude_kwargs or {}
        fields_filter_kwargs = fields_filter_kwargs or {}

        tasks_filter = {'task__workflow_id': self.id, **tasks_filter_kwargs}
        fieldset_filter = {
            f'fieldset__{key}': value
            for key, value in tasks_filter.items()
        }
        tasks_q = Q(**tasks_filter)
        fieldset_q = Q(**fieldset_filter)

        if tasks_exclude_kwargs:
            fieldset_exclude_kwargs = {
                f'fieldset__{key}': value
                for key, value in tasks_exclude_kwargs.items()
            }
            tasks_q = Q(tasks_q, ~Q(**tasks_exclude_kwargs))
            fieldset_q = Q(fieldset_q, ~Q(**fieldset_exclude_kwargs))

        qst = TaskField.objects.filter(tasks_q | fieldset_q)

        if fields_filter_kwargs:
            qst = qst.filter(**fields_filter_kwargs)

        return qst

    @property
    def kickoff_instance(self):
        return self.kickoff.first()

    def get_template_name(self) -> str:
        return (
            self.legacy_template_name if self.is_legacy_template
            else self.template.name
        )

    @property
    def is_delayed(self):
        return self.status == WorkflowStatus.DELAYED

    @property
    def is_running(self):
        return self.status == WorkflowStatus.RUNNING

    @property
    def is_completed(self):
        return self.status == WorkflowStatus.DONE

    def get_kickoff_fields_markdown_values(
        self,
        fields_filter_kwargs: Optional[Dict] = None,
    ) -> Dict[str, str]:
        """Extends parent method by adding the workflow-starter
            system variable to the substitution dictionary."""

        fields_values = super().get_kickoff_fields_markdown_values(
            fields_filter_kwargs=fields_filter_kwargs,
        )

        fields_values['workflow-starter'] = get_workflow_starter_name(
            self.workflow_starter,
        )
        return fields_values

    def get_fields_markdown_values(
        self,
        tasks_filter_kwargs: Optional[Dict] = None,
        tasks_exclude_kwargs: Optional[Dict] = None,
        fields_filter_kwargs: Optional[Dict] = None,
    ) -> Dict[str, str]:
        """Extends parent method by adding the workflow-starter
            system variable to the substitution dictionary."""

        fields_values = super().get_fields_markdown_values(
            tasks_filter_kwargs=tasks_filter_kwargs,
            tasks_exclude_kwargs=tasks_exclude_kwargs,
            fields_filter_kwargs=fields_filter_kwargs,
        )

        fields_values['workflow-starter'] = get_workflow_starter_name(
            self.workflow_starter,
        )
        return fields_values
