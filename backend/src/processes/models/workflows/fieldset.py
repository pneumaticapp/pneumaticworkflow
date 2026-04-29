from django.db import models

from src.accounts.models import AccountBaseMixin
from src.generics.managers import BaseSoftDeleteManager
from src.processes.models.base import BaseApiNameModel
from src.processes.models.mixins import (
    BaseFieldSetMixin,
    BaseFieldSetRuleMixin,
)
from src.processes.models.workflows.kickoff import KickoffValue
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.workflow import Workflow
from src.processes.querysets import FieldSetQuerySet, FieldSetRuleQuerySet


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
    order = models.IntegerField(default=0)

    objects = BaseSoftDeleteManager.from_queryset(FieldSetQuerySet)()


class FieldSetRule(
    BaseApiNameModel,
    BaseFieldSetRuleMixin,
    AccountBaseMixin,
):

    class Meta:
        ordering = ['-id']

    fieldset = models.ForeignKey(
        FieldSet,
        on_delete=models.CASCADE,
        related_name='rules',
    )

    objects = BaseSoftDeleteManager.from_queryset(FieldSetRuleQuerySet)()
