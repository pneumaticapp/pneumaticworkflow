# ruff: noqa: PLC0415
from typing import Optional, Set
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.db.models import UniqueConstraint, Q
from src.accounts.models import (
    AccountBaseMixin,
    UserGroup
)
from src.generics.managers import BaseSoftDeleteManager
from src.processes.models.mixins import (
    TaskMixin,
    TaskRawPerformersMixin
)
from src.processes.querysets import TaskTemplateQuerySet
from src.processes.enums import (
    PerformerType,
    FieldType
)
from src.processes.models.templates.template import Template
from src.processes.models.base import BaseApiNameModel


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
    ancestors = ArrayField(
        base_field=models.CharField(max_length=200),
        default=list,
        help_text='Api names of task ancestors'
    )
    search_content = SearchVectorField(null=True)

    objects = BaseSoftDeleteManager.from_queryset(TaskTemplateQuerySet)()

    def _get_raw_performer(
        self,
        user: Optional[UserModel] = None,
        group: Optional[UserGroup] = None,
        user_id: Optional[int] = None,
        field=None,  # Optional[TaskField]
        performer_type: PerformerType = PerformerType.USER,
        **kwargs
    ):  # -> RawPerformerTemplate

        """ Returns new a raw performer object with given data """

        from src.processes.models.templates.raw_performer\
            import RawPerformerTemplate

        result = RawPerformerTemplate(
            account=self.account,
            task=self,
            template=self.template,
            field=field,
            type=performer_type
        )
        if group:
            result.group = group
        elif user:
            result.user = user
        elif user_id:
            result.user_id = user_id
        return result

    def add_raw_performer(
        self,
        user: Optional[UserModel] = None,
        group: Optional[UserGroup] = None,
        user_id: Optional[int] = None,
        field=None,
        api_name: Optional[str] = None,
        performer_type: PerformerType = PerformerType.USER,
        **kwargs
    ) -> object:

        """ Creates and returns a raw performer for a task with given data """

        if performer_type != PerformerType.WORKFLOW_STARTER:
            if not user and not user_id and not group and not field:
                raise Exception(
                    'Raw performer should be linked with field or user'
                )

        raw_performer = self._get_raw_performer(
            api_name=api_name,
            performer_type=performer_type,
            user=user,
            group=group,
            user_id=user_id,
            field=field
        )
        raw_performer.save()
        return raw_performer

    def get_prev_tasks_fields_api_names(self) -> Set[str]:

        prev_tasks_fields_api_names = self.template.get_fields(
            fields_filter_kwargs={'type': FieldType.USER}
        )
        return set(prev_tasks_fields_api_names.api_names())

    def __str__(self):
        return f'{self.template.name} task {self.number}'
