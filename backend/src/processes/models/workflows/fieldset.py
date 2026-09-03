from django.db import models

from src.accounts.models import AccountBaseMixin
from src.generics.managers import BaseSoftDeleteManager
from src.processes.enums import (
    FieldSetRuleOperator,
)
from src.processes.models.base import BaseApiNameModel
from src.processes.models.mixins import (
    BaseFieldSetMixin,
    BaseFieldSetRuleMixin,
)
from src.processes.models.workflows.kickoff import KickoffValue
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.workflow import Workflow
from src.processes.querysets import (
    FieldSetQuerySet,
    FieldSetRuleQuerySet,
)


class FieldSet(
    BaseApiNameModel,
    BaseFieldSetMixin,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['-id']

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='fieldsets',
    )
    kickoff = models.ForeignKey(
        KickoffValue,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fieldsets',
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fieldsets',
    )

    objects = BaseSoftDeleteManager.from_queryset(FieldSetQuerySet)()


class FieldSetRule(
    BaseApiNameModel,
    BaseFieldSetRuleMixin,
    AccountBaseMixin,
):
    # TODO Deprecated

    class Meta:
        ordering = ['-id']

    fieldset = models.ForeignKey(
        FieldSet,
        on_delete=models.CASCADE,
        related_name='rules',
    )

    objects = BaseSoftDeleteManager.from_queryset(FieldSetRuleQuerySet)()


class FieldSetRuleSet(
    BaseApiNameModel,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['order', 'id']

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='fieldset_rulesets',
    )
    fieldset = models.ForeignKey(
        FieldSet,
        on_delete=models.CASCADE,
        related_name='rulesets',
    )
    message = models.TextField(
        null=True,
        blank=True,
        help_text='custom error message for a type="validator"',
    )
    order = models.PositiveIntegerField(default=0)
    fields = models.ManyToManyField(
        'processes.TaskField',
        blank=True,
        related_name='fieldset_rulesets',
    )

    def __str__(self):
        return f'{self.type} / {self.api_name}'


class FieldSetRuleGroupOr(
    BaseApiNameModel,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['id']

    api_name_prefix = 'fieldset-rule-group-or'
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='fieldset_ruleset_groups_or',
    )
    fieldset_rule = models.ForeignKey(
        FieldSetRuleSet,
        on_delete=models.CASCADE,
        related_name='groups_or',
    )

    def __str__(self):
        return self.api_name


class FieldSetRuleGroupAnd(
    BaseApiNameModel,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['id']

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='fieldset_rules_group_and',
    )
    group_or = models.ForeignKey(
        FieldSetRuleGroupOr,
        on_delete=models.CASCADE,
        related_name='groups_and',
    )
    operator = models.CharField(
        max_length=50,
        choices=FieldSetRuleOperator.CHOICES,
    )
    value = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f'{self.operator} {self.value}'
