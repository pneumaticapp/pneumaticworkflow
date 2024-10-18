from typing import Optional, Dict
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVectorField
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from pneumatic_backend.accounts.models import AccountBaseMixin
from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.generics.models import SoftDeleteModel
from pneumatic_backend.processes.models.mixins import WorkflowMixin
from pneumatic_backend.processes.querysets import (
    WorkflowQuerySet,
    TaskFieldQuerySet,
)
from pneumatic_backend.processes.enums import WorkflowStatus
from pneumatic_backend.processes.models.templates.template import Template

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
    current_task = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    status = models.IntegerField(
        choices=WorkflowStatus.CHOICES,
        default=WorkflowStatus.RUNNING
    )
    status_updated = models.DateTimeField(db_index=True)
    tasks_count = models.IntegerField(null=False)
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
    workflow_starter = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        related_name='started_workflow',
        null=True
    )
    date_completed = models.DateTimeField(null=True)
    due_date = models.DateTimeField(null=True)
    ancestor_task = models.ForeignKey(
        'Task',
        null=True,
        help_text='The task within which the subprocess should be executed',
        on_delete=models.SET_NULL,
        related_name='sub_workflows'
    )

    objects = BaseSoftDeleteManager.from_queryset(WorkflowQuerySet)()

    search_content = SearchVectorField(null=True)

    @property
    def current_task_instance(self):
        return self.tasks.get(number=self.current_task)

    def as_json(self):
        wf = self.template
        kickoff = self.kickoff_instance
        current_task = self.current_task_instance
        current_task_performers = [
            {
                'id': x.id,
                'first_name': x.first_name,
                'last_name': x.last_name
            } for x in current_task.performers.exclude_directly_deleted()
        ]
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'date_created': self.date_created,
            'date_created_tsp': (
                self.date_created.timestamp()
                if self.date_created else None
            ),
            'template': {
                'id': wf.id,
                'name': wf.name
            } if wf else None,
            'current_task': {
                'id': current_task.id,
                'name': current_task.name,
                'number': current_task.number,
                'description': current_task.description,
                'date_started': current_task.date_started,
                'date_started_tsp': (
                    current_task.date_started.timestamp()
                    if current_task.date_started else None
                ),
                'date_completed': current_task.date_completed,
                'date_completed_tsp': (
                    current_task.date_completed.timestamp()
                    if current_task.date_completed else None
                ),
                'due_date': current_task.due_date,
                'due_date_tsp': (
                    current_task.due_date.timestamp()
                    if current_task.due_date else None
                ),
                'performers': current_task_performers
            },
            'kickoff': {
                'id': kickoff.id,
                'description': kickoff.description,
                'output': [
                    {
                        'id': field.id,
                        'type': field.type,
                        'is_required': field.is_required,
                        'name': field.name,
                        'description': field.description,
                        'api_name': field.api_name,
                        'value': field.value,
                        'user_id': field.user_id,
                        'selections': [
                            {
                                'id': selection.id,
                                'value': selection.value,
                                'is_selected': selection.is_selected,
                            } for selection in field.selections.all()
                        ],
                        'attachments': [
                            {
                                'id': attachment.id,
                                'name': attachment.name,
                                'url': attachment.url,
                            } for attachment in field.attachments.all()
                        ]
                    } for field in kickoff.output.all()
                ]
            }
        }

    def serialize_hook(self, hook):
        hook_dict = hook.dict()
        return {
            'hook': hook_dict,
            'workflow': self.as_json()
        }

    def __str__(self):
        return f'(Workflow {self.id}) {self.name}'

    def is_version_lower(self, version):
        return version > self.version

    def save(self, update_fields=None, **kwargs):
        if update_fields is not None:
            if 'status' in update_fields:
                self.status_updated = timezone.now()
                update_fields.append('status_updated')
        super().save(update_fields=update_fields, **kwargs)

    def _get_kickoff(self):
        kickoff = self.kickoff.prefetch_related('output__selections').first()
        if not kickoff:
            from pneumatic_backend.processes.models.workflows\
                .kickoff import KickoffValue
            kickoff = KickoffValue(
                workflow=self,
                account_id=self.account_id
            )
        return kickoff

    def _get_task(self, number, tasks):
        for task in tasks:
            if task.number == number:
                return task
        from pneumatic_backend.processes.models.workflows \
            .task import Task
        return Task(
            workflow=self,
            number=number
        )

    def get_kickoff_output_fields(
        self,
        fields_filter_kwargs: Optional[Dict] = None
    ) -> TaskFieldQuerySet:

        """ Return the output fields from kickoff """

        try:
            result = self.kickoff.get().output.all()
            if fields_filter_kwargs:
                result = result.filter(**fields_filter_kwargs)
        except ObjectDoesNotExist:
            from pneumatic_backend.processes.models.workflows \
                .fields import TaskField
            result = TaskField.objects.none()
        return result

    def get_tasks_output_fields(
        self,
        tasks_filter_kwargs: Optional[Dict] = None,
        fields_filter_kwargs: Optional[Dict] = None
    ) -> TaskFieldQuerySet:

        """ Return the output fields from tasks """
        tasks = self.tasks.all()
        if tasks_filter_kwargs:
            tasks = tasks.filter(**tasks_filter_kwargs)
        tasks_ids = tasks.values_list('id', flat=True)

        if not fields_filter_kwargs:
            fields_filter_kwargs = {}
        fields_filter_kwargs['task_id__in'] = tasks_ids
        from pneumatic_backend.processes.models.workflows.fields import \
            TaskField
        return TaskField.objects.filter(**fields_filter_kwargs)

    @property
    def kickoff_instance(self):
        return self.kickoff.first()

    def can_be_finished_by(self, user: UserModel) -> bool:

        """ Check user permission to finish workflow

            Finish allow:
            - current task performers
            - workflow template owners
            - account owner
        """

        result = True
        current_task = self.current_task_instance
        performers = current_task.taskperformer_set.exclude_directly_deleted()
        is_performer = (
            user.id in performers.values_list(
                'user_id', flat=True
            )
        )
        if not is_performer:
            if not self.is_legacy_template:
                is_template_owner = (
                    user in self.template.template_owners.all()
                )
                if not is_template_owner:
                    is_account_owner = (
                        user.is_account_owner
                        and user.account_id == self.account_id
                    )
                    if not is_account_owner:
                        result = False
        return result

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
