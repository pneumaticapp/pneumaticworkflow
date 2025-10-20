from django.db import models

from src.generics.managers import BaseSoftDeleteManager
from src.generics.models import SoftDeleteModel
from src.processes.models.mixins import (
    ApiNameMixin,
    ConditionMixin,
    PredicateMixin,
)
from src.processes.models.workflows.task import Task
from src.processes.querysets import ConditionQuerySet


class Condition(
    SoftDeleteModel,
    ConditionMixin,
    ApiNameMixin,
):

    class Meta:
        ordering = ('order', )

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='conditions',
    )
    objects = BaseSoftDeleteManager.from_queryset(ConditionQuerySet)()


class Rule(
    SoftDeleteModel,
    ApiNameMixin,
):

    condition = models.ForeignKey(
        Condition,
        on_delete=models.CASCADE,
        related_name='rules',
    )


class Predicate(
    SoftDeleteModel,
    PredicateMixin,
    ApiNameMixin,
):

    rule = models.ForeignKey(
        Rule,
        on_delete=models.CASCADE,
        related_name='predicates',
    )
