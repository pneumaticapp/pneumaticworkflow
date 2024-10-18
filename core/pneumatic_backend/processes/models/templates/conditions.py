from django.db import models
from django.db.models import UniqueConstraint, Q
from pneumatic_backend.processes.models.base import (
    BaseApiNameModel
)
from pneumatic_backend.processes.models.mixins import (
    ConditionMixin,
    PredicateMixin,
)
from pneumatic_backend.processes.models.templates.template import Template
from pneumatic_backend.processes.models.templates.task import TaskTemplate


class ConditionTemplate(
    BaseApiNameModel,
    ConditionMixin
):

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name'],
                condition=Q(is_deleted=False),
                name='processes_conditiontemplate_template_api_name_unique',
            )
        ]

    api_name_prefix = 'condition'

    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='conditions',
    )
    task = models.ForeignKey(
        TaskTemplate,
        on_delete=models.CASCADE,
        related_name='conditions',
    )


class RuleTemplate(
    BaseApiNameModel
):

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name'],
                condition=Q(is_deleted=False),
                name='processes_ruletemplate_template_api_name_unique',
            )
        ]
    api_name_prefix = 'rule'

    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='rules',
    )
    condition = models.ForeignKey(
        ConditionTemplate,
        on_delete=models.CASCADE,
        related_name='rules'
    )


class PredicateTemplate(
    BaseApiNameModel,
    PredicateMixin
):

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['template', 'api_name'],
                condition=Q(is_deleted=False),
                name='processes_predicatetemplate_template_api_name_unique',
            )
        ]

    api_name_prefix = 'predicate'

    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='predicates',
    )
    rule = models.ForeignKey(
        RuleTemplate,
        on_delete=models.CASCADE,
        related_name='predicates',
    )
