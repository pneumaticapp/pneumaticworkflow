from django.contrib.auth import get_user_model
from django.db import models

from src.accounts.models import AccountBaseMixin
from src.generics.managers import BaseSoftDeleteManager
from src.generics.models import SoftDeleteModel
from src.processes.enums import FieldRuleType, FieldRuleOperator
from src.processes.models.base import BaseApiNameModel
from src.processes.models.mixins import (
    ApiNameMixin,
    FieldMixin,
)
from src.processes.models.workflows.kickoff import KickoffValue
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.fieldset import FieldSet
from src.processes.models.workflows.workflow import Workflow
from src.processes.querysets import (
    FieldSelectionQuerySet,
    TaskFieldQuerySet,
)

UserModel = get_user_model()


class TaskField(
    SoftDeleteModel,
    AccountBaseMixin,
    FieldMixin,
    ApiNameMixin,
):

    class Meta:
        ordering = ['-order', 'id']

    value = models.TextField(
        blank=True,
        help_text='Human readable value',
    )
    clear_value = models.TextField(
        null=True,
        blank=True,
        help_text='Does not contains markdown',
    )
    markdown_value = models.TextField(
        null=True,
        blank=True,
        help_text='Contains markdown representation',
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
    fieldset = models.ForeignKey(
        FieldSet,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fields',
    )
    rules = models.ManyToManyField(
        'processes.FieldsetRule',
        blank=True,
        related_name='fields',
    )
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='fields',
    )
    objects = BaseSoftDeleteManager.from_queryset(TaskFieldQuerySet)()

    def __str__(self):
        return f'{self.type}: {self.value}'


class FieldSelection(
    SoftDeleteModel,
    ApiNameMixin,
):

    class Meta:
        ordering = ['pk']

    field = models.ForeignKey(
        TaskField,
        on_delete=models.CASCADE,
        related_name='selections',
    )
    value = models.CharField(max_length=200)

    objects = BaseSoftDeleteManager.from_queryset(
        FieldSelectionQuerySet,
    )()

    def __str__(self):
        return self.value


class FieldRuleSet(
    BaseApiNameModel,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['order', 'id']

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='field_rulesets',
    )
    field = models.ForeignKey(
        TaskField,
        on_delete=models.CASCADE,
        related_name='rulesets',
    )
    type = models.CharField(
        max_length=50,
        choices=FieldRuleType.CHOICES,
    )
    message = models.TextField(
        null=True,
        blank=True,
        help_text='custom error message for a type="validator"',
    )
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.api_name


class FieldRuleGroupOr(
    BaseApiNameModel,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['id']

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='field_ruleset_groups_or',
    )
    ruleset = models.ForeignKey(
        FieldRuleSet,
        on_delete=models.CASCADE,
        related_name='groups_or',
    )

    def __str__(self):
        return self.api_name


class FieldRuleGroupAnd(
    BaseApiNameModel,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['id']

    api_name_prefix = 'field-rule-group-and'
    group_or = models.ForeignKey(
        FieldRuleGroupOr,
        on_delete=models.CASCADE,
        related_name='groups_and',
    )
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='field_rules_group_and',
    )
    operator = models.CharField(
        max_length=50,
        choices=FieldRuleOperator.CHOICES,
    )
    value = models.CharField(max_length=200, null=True, blank=True)
    field = models.CharField(
        max_length=200,
        null=True,
    )

    def __str__(self):
        return self.api_name
