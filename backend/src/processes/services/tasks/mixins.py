from typing import TYPE_CHECKING, Dict, List, Optional, Type

from django.contrib.auth import get_user_model

from src.processes.services.base import BaseUpdateVersionService
from src.processes.services.tasks.fields.field_ruleset import (
    FieldRuleSetVersionService,
)
from src.processes.services.workflows.fieldsets.fieldset_ruleset import (
    FieldSetRuleSetVersionService,
)
from src.processes.models.workflows.conditions import (
    Predicate,
    Rule,
)

if TYPE_CHECKING:
    from src.processes.models.workflows.fields import (
        TaskField,
    )
    from src.processes.models.workflows.fieldset import (
        FieldSet,
    )

UserModel = get_user_model()


class RuleSetVersionMixin:

    """ The fieldset branch of the task and kickoff version
        services is the same, only the parent differs. """

    def _update_rulesets(
        self,
        parent,
        rulesets_data: Optional[List[Dict]],
        version: int,
        service_cls: Type[BaseUpdateVersionService],
        parent_kwarg: str,
    ):

        # Absent key = snapshot predates rulesets, keep as-is.
        # Empty list = no rulesets, delete all.
        if rulesets_data is None:
            return
        api_names = set()
        for ruleset_data in rulesets_data:
            service = service_cls(
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
            )
            service.update_from_version(
                data=ruleset_data,
                version=version,
                **{parent_kwarg: parent},
            )
            api_names.add(ruleset_data['api_name'])
        parent.rulesets.exclude(api_name__in=api_names).delete()

    def _update_fieldset_rulesets(
        self,
        fieldset: 'FieldSet',
        rulesets_data: Optional[List[Dict]] = None,
        *,
        version: int,
    ):
        self._update_rulesets(
            parent=fieldset,
            rulesets_data=rulesets_data,
            version=version,
            service_cls=FieldSetRuleSetVersionService,
            parent_kwarg='fieldset',
        )

    def _update_field_rulesets(
        self,
        field: 'TaskField',
        rulesets_data: Optional[List[Dict]] = None,
        *,
        version: int,
    ):
        self._update_rulesets(
            parent=field,
            rulesets_data=rulesets_data,
            version=version,
            service_cls=FieldRuleSetVersionService,
            parent_kwarg='field',
        )


class ConditionMixin:

    @staticmethod
    def create_rules(
        conditions,
        conditions_tree,
    ):

        # TODO Move to RuleService

        rules = []
        rules_tree = {}
        for condition in conditions:
            for rule, predicates in conditions_tree[condition.api_name]:
                rule.condition = condition
                rules.append(rule)
                rules_tree[rule.api_name] = predicates

        rules = Rule.objects.bulk_create(rules)
        ConditionMixin._create_predicates(rules, rules_tree)

    @staticmethod
    def _create_predicates(
        rules: List[Rule],
        rules_tree: dict,
    ):

        # TODO Move to PredicateService

        predicates = []
        for rule in rules:
            predicates_by_rule = rules_tree[rule.api_name]
            for predicate in predicates_by_rule:
                predicate.rule = rule
                predicates.append(predicate)
        Predicate.objects.bulk_create(predicates)
