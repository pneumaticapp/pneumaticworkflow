from django.db import models
from django.db.models import Q, UniqueConstraint

from src.accounts.models import AccountBaseMixin
from src.generics.managers import BaseSoftDeleteManager
from src.processes.models.base import BaseApiNameModel
from src.processes.models.mixins import (
    BaseFieldSetMixin,
    BaseFieldSetRuleMixin,
)
from src.processes.models.templates.kickoff import Kickoff
from src.processes.models.templates.template import Template
from src.processes.models.templates.task import TaskTemplate
from src.processes.querysets import (
    FieldsetTemplateQuerySet,
    FieldsetTemplateRuleQuerySet,
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
                fields=['account', 'api_name'],
                condition=Q(is_deleted=False),
                name='fieldsettemplate_account_api_name_unique',
            ),
        ]

    api_name_prefix = 'fieldset'

    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='fieldsets',
        null=True,
        blank=True,
    )
    task = models.ForeignKey(
        TaskTemplate,
        on_delete=models.SET_NULL,
        related_name='fieldsets',
        null=True,
        blank=True,
    )
    kickoff = models.ForeignKey(
        Kickoff,
        on_delete=models.SET_NULL,
        related_name='fieldsets',
        null=True,
        blank=True,
    )

    objects = BaseSoftDeleteManager.from_queryset(
        FieldsetTemplateQuerySet,
    )()

    def __str__(self):
        return self.name


class FieldsetTemplateRule(
    BaseApiNameModel,
    BaseFieldSetRuleMixin,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['-id']

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
