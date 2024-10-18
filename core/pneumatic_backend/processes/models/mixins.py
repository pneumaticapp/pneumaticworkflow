from abc import abstractmethod
from typing import Dict, Optional
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from django.core.validators import MinValueValidator
from django.db import models
from pneumatic_backend.processes.enums import PerformerType
from pneumatic_backend.processes.enums import (
    FieldType,
    PredicateType,
    PredicateOperator
)


UserModel = get_user_model()


class RawPerformerMixin(models.Model):

    class Meta:
        abstract = True

    type = models.CharField(
        max_length=100,
        choices=PerformerType.choices
    )
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        null=True
    )


class WorkflowMixin(models.Model):

    class Meta:
        abstract = True

    description = models.TextField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    finalizable = models.BooleanField(default=False)
    version = models.IntegerField(default=0)

    @abstractmethod
    def get_kickoff_output_fields(
        self,
        fields_filter_kwargs: Optional[Dict] = None
    ) -> QuerySet:

        """ Return the output fields from kickoff """

    @abstractmethod
    def get_tasks_output_fields(
        self,
        tasks_filter_kwargs: Optional[Dict] = None,
        fields_filter_kwargs: Optional[Dict] = None
    ) -> QuerySet:

        """ Return the output fields from tasks """

    def get_fields(
        self,
        tasks_filter_kwargs: Optional[Dict] = None,
        fields_filter_kwargs: Optional[Dict] = None
    ) -> QuerySet:

        """ Return the output fields from kickoff and tasks """

        kickoff_fields_qst = self.get_kickoff_output_fields(
            fields_filter_kwargs=fields_filter_kwargs
        )
        tasks_fields_qst = self.get_tasks_output_fields(
            tasks_filter_kwargs=tasks_filter_kwargs,
            fields_filter_kwargs=fields_filter_kwargs
        )
        return kickoff_fields_qst.union(tasks_fields_qst)

    def get_fields_as_dict(
        self,
        tasks_filter_kwargs: Optional[Dict] = None,
        fields_filter_kwargs: Optional[Dict] = None,
        dict_key: Optional[str] = None
    ) -> dict:

        """ Returns fields mapped by field attribute
            {field.attribute: field, ...} """

        fields = self.get_fields(
            tasks_filter_kwargs=tasks_filter_kwargs,
            fields_filter_kwargs=fields_filter_kwargs
        )
        result = {}
        for field in fields:
            result[getattr(field, dict_key)] = field
        return result

    def get_kickoff_fields_values(self) -> Dict[str, str]:

        """ Returns fields markdown representations mapped by field api_name
            {field.api_name: str} """

        fields = self.get_kickoff_output_fields()
        values = {field.api_name: field.value for field in fields}
        return values

    def get_fields_markdown_values(
        self,
        tasks_filter_kwargs: Optional[Dict] = None,
        fields_filter_kwargs: Optional[Dict] = None
    ) -> Dict[str, str]:

        """ Returns fields markdown representations mapped by field api_name
            {field.api_name: str} """

        fields = self.get_fields(
            tasks_filter_kwargs=tasks_filter_kwargs,
            fields_filter_kwargs=fields_filter_kwargs
        )
        values = {field.api_name: field.markdown_value for field in fields}
        return values


class TaskMixin(models.Model):

    class Meta:
        abstract = True

    description = models.TextField(null=True, blank=True)
    number = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    require_completion_by_all = models.BooleanField(default=False)

    def is_first(self):
        return self.number == 1


class FieldMixin(models.Model):

    class Meta:
        abstract = True

    name = models.CharField(max_length=120)
    type = models.CharField(
        choices=FieldType.CHOICES,
        max_length=10
    )
    description = models.TextField(null=True, blank=True)
    is_required = models.BooleanField(default=False)
    order = models.IntegerField(default=0)


class ConditionMixin(models.Model):

    class Meta:
        abstract = True

    SKIP_TASK = 'skip_task'
    START_TASK = 'start_task'
    END_WORKFLOW = 'end_process'
    ACTION_TYPES = (
        (SKIP_TASK, 'Skip task'),
        (START_TASK, 'Start task'),
        (END_WORKFLOW, 'End workflow'),
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_TYPES,
    )
    order = models.PositiveSmallIntegerField(default=0)


class PredicateMixin(models.Model):

    class Meta:
        abstract = True

    operator = models.CharField(
        choices=PredicateOperator.CHOICES,
        max_length=30,
    )
    # TODO Rename to source_id
    field = models.CharField(
        max_length=200,
        null=True,
    )
    # TODO Rename to source_type
    field_type = models.CharField(
        choices=PredicateType.CHOICES,
        max_length=20,
    )
    value = models.CharField(
        null=True,
        max_length=200,
    )


class TaskRawPerformersMixin:

    @abstractmethod
    def _get_raw_performer(
        self,
        api_name: str,
        performer_type: PerformerType = PerformerType.USER,
        user: Optional[UserModel] = None,
        user_id: Optional[int] = None,
        field=None,
        **kwargs
    ):

        """ Returns new a raw performer object with given data """

    @abstractmethod
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

    def delete_raw_performer(
        self,
        user: Optional[UserModel] = None,
        field=None,
        performer_type: PerformerType = PerformerType.USER
    ) -> int:

        """ Delete a raw_performer
            and returns the number of objects deleted """

        if performer_type != PerformerType.WORKFLOW_STARTER:
            if user is None and field is None:
                raise Exception(
                    'Raw performer should be linked with field or user'
                )

        return self.raw_performers.filter(
            type=performer_type,
            user=user,
            field=field
        ).delete()[0]

    def delete_raw_performers(self):

        """ Delete all raw performers """

        self.raw_performers.all().delete()


class ApiNameMixin(models.Model):

    class Meta:
        abstract = True

    api_name = models.CharField(max_length=200)
