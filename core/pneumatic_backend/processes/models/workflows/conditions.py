from django.db import models
from pneumatic_backend.generics.models import SoftDeleteModel
from pneumatic_backend.processes.models.mixins import (
    ConditionMixin,
    PredicateMixin,
    ApiNameMixin,
)
from pneumatic_backend.processes.models.workflows.task import Task


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


class Rule(
    SoftDeleteModel,
    ApiNameMixin,
):

    condition = models.ForeignKey(
        Condition,
        on_delete=models.CASCADE,
        related_name='rules'
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
