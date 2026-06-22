from django.db import models
from django.db.models import Q, UniqueConstraint

from src.accounts.models import AccountBaseMixin
from src.generics.managers import BaseSoftDeleteManager
from src.processes.enums import FieldRuleType, FieldRuleOperator
from src.processes.models.base import BaseApiNameModel
from src.processes.models.mixins import (
    FieldMixin,
)
from src.processes.models.templates.kickoff import Kickoff
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.templates.template import Template
from src.processes.querysets import (
    FieldTemplateQuerySet,
    FieldTemplateValuesQuerySet,
)


class FieldTemplate(
    BaseApiNameModel,
    AccountBaseMixin,
    FieldMixin,
):

    class Meta:
        ordering = ['-order']
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name', 'account'],
                condition=Q(is_deleted=False),
                name='processes_fieldtemplate_template_api_name_unique',
            ),
        ]

    api_name_prefix = 'field'

    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fields',
    )
    kickoff = models.ForeignKey(
        Kickoff,
        on_delete=models.CASCADE,
        null=True,
        related_name='fields',
    )
    task = models.ForeignKey(
        TaskTemplate,
        on_delete=models.CASCADE,
        null=True,
        related_name='fields',
    )
    fieldset = models.ForeignKey(
        'processes.FieldsetTemplate',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fields',
    )
    # TODO Deprecated
    rules = models.ManyToManyField(
        'processes.FieldsetTemplateRuleOld',
        blank=True,
        related_name='fields',
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
                fields=['template', 'api_name', 'account'],
                condition=Q(is_deleted=False),
                name=(
                    'processes_fieldtemplateselection'
                    '_template_api_name_unique'
                ),
            ),
            UniqueConstraint(
                fields=['field_template', 'value'],
                condition=Q(is_deleted=False),
                name=(
                    'processes_fieldtemplateselection'
                    '_field_template_value_unique'
                ),
            ),
        ]

    api_name_prefix = 'selection'

    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='selections',
    )
    field_template = models.ForeignKey(
        FieldTemplate,
        on_delete=models.CASCADE,
        related_name='selections',
    )
    value = models.CharField(max_length=200)

    objects = BaseSoftDeleteManager.from_queryset(
        FieldTemplateValuesQuerySet,
    )()


class FieldTemplateRuleSet(
    BaseApiNameModel,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['order', 'id']
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name', 'account'],
                condition=Q(is_deleted=False),
                name='fieldtemplateruleset_field_api_name_unique',
            ),
        ]

    api_name_prefix = 'field-ruleset'
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='field_rulesets',
    )
    field = models.ForeignKey(
        FieldTemplate,
        on_delete=models.CASCADE,
        related_name='rule_sets',
    )
    type = models.CharField(
        max_length=50,
        choices=FieldRuleType.CHOICES,
    )
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.api_name


class FieldTemplateRuleGroupOr(
    BaseApiNameModel,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['id']
        constraints = [
            UniqueConstraint(
                fields=['api_name', 'template', 'account'],
                condition=Q(is_deleted=False),
                name='rulegroupor_field_rule_api_name_unique',
            ),
        ]

    api_name_prefix = 'field-rule-group-or'
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='field_ruleset_groups_or',
    )
    field_rule = models.ForeignKey(
        FieldTemplateRuleSet,
        on_delete=models.CASCADE,
        related_name='groups_or',
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.api_name


class FieldTemplateRuleGroupAnd(
    BaseApiNameModel,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['id']
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name', 'account'],
                condition=Q(is_deleted=False),
                name='rulegroupand_group_or_api_name_unique',
            ),
        ]

    api_name_prefix = 'field-rule-group-and'
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='field_ruleset_groups_and',
    )
    group_or = models.ForeignKey(
        FieldTemplateRuleGroupOr,
        on_delete=models.CASCADE,
        related_name='groups_and',
    )

    def __str__(self):
        return self.api_name


class FieldTemplateRule(
    BaseApiNameModel,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['id']
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name', 'account'],
                condition=Q(is_deleted=False),
                name='fieldtemplaterule_group_and_api_name_unique',
            ),
        ]

    api_name_prefix = 'field-rule'
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='field_rules',
    )
    group_and = models.ForeignKey(
        FieldTemplateRuleGroupAnd,
        on_delete=models.CASCADE,
        related_name='field_rules',
    )
    operator = models.CharField(
        max_length=50,
        choices=FieldRuleOperator.CHOICES,
    )
    value = models.CharField(max_length=200, null=True, blank=True)
    field = models.ForeignKey(
        FieldTemplate,
        on_delete=models.CASCADE,
        related_name='field_rules',
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.api_name
