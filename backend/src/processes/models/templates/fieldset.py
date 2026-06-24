from django.db import models
from django.db.models import Q, UniqueConstraint

from src.accounts.models import AccountBaseMixin
from src.generics.managers import BaseSoftDeleteManager
from src.processes.enums import FieldSetRuleType, FieldSetRuleOperator
from src.processes.models.base import BaseApiNameModel
from src.processes.models.mixins import (
    BaseFieldSetMixin, BaseFieldSetRuleMixin,
)
from src.processes.models.templates.kickoff import Kickoff
from src.processes.models.templates.template import Template
from src.processes.models.templates.task import TaskTemplate
from src.processes.querysets import (
    FieldsetTemplateQuerySet, FieldsetTemplateRuleQuerySet,
)


class FieldsetTemplate(
    BaseApiNameModel,
    BaseFieldSetMixin,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['-id']
        constraints = [
            UniqueConstraint(
                fields=['api_name', 'template', 'is_shared', 'account'],
                condition=Q(is_deleted=False),
                name='fieldsettemplate_api_name_template_unique',
            ),
        ]

    api_name_prefix = 'fieldset'

    date_created = models.DateTimeField(
        auto_now_add=True,
    )
    is_shared = models.BooleanField(default=True)
    shared_fieldset = models.ForeignKey(
        'FieldsetTemplate',
        on_delete=models.SET_NULL,
        related_name='child_fieldsets',
        null=True,
        blank=True,
    )
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='fieldsets',
        null=True,
        blank=True,
    )
    task = models.ForeignKey(
        TaskTemplate,
        on_delete=models.CASCADE,
        related_name='fieldsets',
        null=True,
        blank=True,
    )
    kickoff = models.ForeignKey(
        Kickoff,
        on_delete=models.CASCADE,
        related_name='fieldsets',
        null=True,
        blank=True,
    )

    objects = BaseSoftDeleteManager.from_queryset(
        FieldsetTemplateQuerySet,
    )()

    def __str__(self):
        return self.name


class FieldsetTemplateRuleOld(
    BaseApiNameModel,
    BaseFieldSetRuleMixin,
    AccountBaseMixin,
):

    # TODO Deprecated

    class Meta:
        ordering = ['-id']
        db_table = 'processes_fieldsettemplate_rule_old'
        constraints = [
            UniqueConstraint(
                fields=['api_name', 'fieldset'],
                condition=Q(is_deleted=False),
                name='fieldsettemplate_api_name_template_unique',
            ),
        ]

    api_name_prefix = 'fieldsetrule'

    fieldset = models.ForeignKey(
        FieldsetTemplate,
        on_delete=models.CASCADE,
        related_name='rules',
    )

    objects = BaseSoftDeleteManager.from_queryset(
        FieldsetTemplateRuleQuerySet,
    )()

    def __str__(self):
        return self.name


class FieldSetTemplateRuleSet(
    BaseApiNameModel,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['order', 'id']
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name', 'account'],
                condition=Q(is_deleted=False),
                name='fieldsetruleset_fieldset_api_name_unique',
            ),
        ]

    api_name_prefix = 'fieldset-ruleset'
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fieldset_rulesets',
    )
    fieldset = models.ForeignKey(
        FieldsetTemplate,
        on_delete=models.CASCADE,
        related_name='rulesets',
    )
    type = models.CharField(
        max_length=50,
        choices=FieldSetRuleType.CHOICES,
    )
    message = models.TextField(
        null=True,
        blank=True,
        help_text='custom error message for a type="validator"',
    )
    order = models.PositiveIntegerField(default=0)
    fields = models.ManyToManyField(
        'processes.FieldTemplate',
        blank=True,
        related_name='fieldset_validator_rulesets',
    )

    def __str__(self):
        return f'{self.fieldset_id} / {self.type} / {self.api_name}'


class FieldSetTemplateRuleGroupOr(
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

    api_name_prefix = 'fieldset-rule-group-or'
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fieldset_ruleset_groups_or',
    )
    fieldset_rule = models.ForeignKey(
        FieldSetTemplateRuleSet,
        on_delete=models.CASCADE,
        related_name='group_or',
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.api_name


class FieldSetTemplateRuleGroupAnd(
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

    api_name_prefix = 'fieldset-rule-group-and'
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fieldset_ruleset_groups_and',
    )
    group_or = models.ForeignKey(
        FieldSetTemplateRuleGroupOr,
        on_delete=models.CASCADE,
        related_name='group_and',
    )

    def __str__(self):
        return self.api_name


class FieldSetTemplateRule(
    BaseApiNameModel,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['id']
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name', 'account'],
                condition=Q(is_deleted=False),
                name='fieldsetrulecondition_group_and_api_name_unique',
            ),
        ]

    api_name_prefix = 'fieldset-rule'
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ruleset_rules',
    )
    group_and = models.ForeignKey(
        FieldSetTemplateRuleGroupAnd,
        on_delete=models.CASCADE,
        related_name='ruleset_rules',
    )
    operator = models.CharField(
        max_length=50,
        choices=FieldSetRuleOperator.CHOICES,
    )
    value = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f'{self.operator} {self.value}'
