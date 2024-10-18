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
    # TODO deprecate template_id, use api_name
    template_id = models.IntegerField(null=True)


class Rule(
    SoftDeleteModel,
    ApiNameMixin,
):

    condition = models.ForeignKey(
        Condition,
        on_delete=models.CASCADE,
        related_name='rules'
    )
    # TODO deprecate template_id, use api_name
    template_id = models.IntegerField(null=True)


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
    # TODO deprecate template_id, use api_name
    template_id = models.IntegerField(null=True)
