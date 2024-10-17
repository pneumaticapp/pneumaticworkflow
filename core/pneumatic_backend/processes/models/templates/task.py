from typing import Optional, Dict, Set
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.db.models import UniqueConstraint, Q, QuerySet
from pneumatic_backend.accounts.models import AccountBaseMixin
from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.processes.models.mixins import (
    TaskMixin,
    TaskRawPerformersMixin
)
from pneumatic_backend.processes.querysets import TaskTemplateQuerySet
from pneumatic_backend.processes.enums import (
    PerformerType,
    FieldType
)
from pneumatic_backend.processes.models.templates.template import Template
from pneumatic_backend.processes.models.base import BaseApiNameModel


UserModel = get_user_model()


class TaskTemplate(
    BaseApiNameModel,
    AccountBaseMixin,
    TaskMixin,
    TaskRawPerformersMixin,
):

    NAME_MAX_LENGTH = 280

    class Meta:
        ordering = ['number']
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name'],
                condition=Q(is_deleted=False),
                name='processes_tasktemplate_template_api_name_unique',
            )
        ]

    api_name_prefix = 'task'
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    delay = models.DurationField(
        blank=True,
        null=True,
    )
    search_content = SearchVectorField(null=True)

    objects = BaseSoftDeleteManager.from_queryset(TaskTemplateQuerySet)()

    @property
    def next(self):
        try:
            return TaskTemplate.objects.get(
                number=self.number + 1,
                template=self.template
            )
        except TaskTemplate.DoesNotExist:
            return None

    @property
    def prev(self):
        try:
            return TaskTemplate.objects.get(
                number=self.number - 1,
                template=self.template
            )
        except TaskTemplate.DoesNotExist:
            return None

    def _get_raw_performer(
        self,
        user: Optional[UserModel] = None,
        user_id: Optional[int] = None,
        field=None,  # Optional[TaskField]
        performer_type: PerformerType = PerformerType.USER,
        **kwargs
    ):  # -> RawPerformerTemplate

        """ Returns new a raw performer object with given data """

        from pneumatic_backend.processes.models.templates.raw_performer\
            import RawPerformerTemplate

        result = RawPerformerTemplate(
            account=self.account,
            task=self,
            template=self.template,
            field=field,
            type=performer_type
        )
        if user:
            result.user = user
        elif user_id:
            result.user_id = user_id
        return result

    def add_raw_performer(
        self,
        user: Optional[UserModel] = None,
        user_id: Optional[int] = None,
        field=None,
        api_name: Optional[str] = None,
        performer_type: PerformerType = PerformerType.USER,
        **kwargs
    ) -> object:

        """ Creates and returns a raw performer for a task with given data """

        if performer_type != PerformerType.WORKFLOW_STARTER:
            if not user and not user_id and not field:
                raise Exception(
                    'Raw performer should be linked with field or user'
                )

        raw_performer = self._get_raw_performer(
            api_name=api_name,
            performer_type=performer_type,
            user=user,
            user_id=user_id,
            field=field
        )
        raw_performer.save()
        return raw_performer

    def get_prev_tasks_fields(
        self,
        fields_filter_kwargs: Optional[Dict] = None
    ) -> QuerySet:  # -> FieldTemplateQuerySet

        """ Returns previous template tasks fields filtered by
            fields_filter_kwargs, example:

            fields_filter_kwargs={
                'type': FieldType.USER
            }
        """

        return self.template.get_fields(
            tasks_filter_kwargs={
                'number__lt': self.number
            },
            fields_filter_kwargs=fields_filter_kwargs
        )

    def get_prev_tasks_fields_api_names(self) -> Set[str]:
        prev_tasks_fields_api_names = self.get_prev_tasks_fields(
            fields_filter_kwargs={'type': FieldType.USER}
        )
        return set(prev_tasks_fields_api_names.api_names())

    def __str__(self):
        return f'{self.template.name} task {self.number}'
