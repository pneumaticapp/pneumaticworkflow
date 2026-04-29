from django.db import models
from django.db.models import Q, UniqueConstraint

from src.accounts.models import AccountBaseMixin
from src.generics.managers import BaseSoftDeleteManager
from src.generics.models import SoftDeleteModel
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
    FieldsetTemplateTaskTemplateQuerySet, FieldsetTemplateKickoffQuerySet,
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

    date_created = models.DateTimeField(
        auto_now_add=True,
    )
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='fieldsets',
    )
    tasks = models.ManyToManyField(
        TaskTemplate,
        through='FieldsetTemplateTaskTemplate',
        related_name='fieldsets',
        blank=True,
    )
    kickoffs = models.ManyToManyField(
        Kickoff,
        through='FieldsetTemplateKickoff',
        related_name='fieldsets',
        blank=True,
    )

    objects = BaseSoftDeleteManager.from_queryset(
        FieldsetTemplateQuerySet,
    )()

    def __str__(self):
        return self.name


class FieldsetTemplateTaskTemplate(SoftDeleteModel):

    """
        Model for the relationship between
        "TaskTemplate" <- m2m -> "FieldsetTemplate"
    """

    class Meta:
        ordering = ['order']
        db_table = 'processes_fieldsettemplate_tasktemplate'

    fieldset = models.ForeignKey(
        'FieldsetTemplate',
        on_delete=models.CASCADE,
    )
    task = models.ForeignKey(
        TaskTemplate,
        on_delete=models.CASCADE,
    )
    order = models.IntegerField(default=0)

    objects = BaseSoftDeleteManager.from_queryset(
        FieldsetTemplateTaskTemplateQuerySet,
    )()

    def __str__(self):
        return (
            f'{self.fieldset_template} - {self.task_template} '
            f'(order={self.order})'
        )


class FieldsetTemplateKickoff(SoftDeleteModel):

    """
        Model for the relationship
        "Kickoff" <- m2m -> "FieldsetTemplate"
    """

    class Meta:
        ordering = ['order']
        db_table = 'processes_fieldsettemplate_kickoff'

    fieldset = models.ForeignKey(
        'FieldsetTemplate',
        on_delete=models.CASCADE,
    )
    kickoff = models.ForeignKey(
        Kickoff,
        on_delete=models.CASCADE,
    )
    order = models.IntegerField(default=0)

    objects = BaseSoftDeleteManager.from_queryset(
        FieldsetTemplateKickoffQuerySet,
    )()

    def __str__(self):
        return f'{self.fieldset_template} - kickoff (order={self.order})'


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
