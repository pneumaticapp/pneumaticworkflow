from typing import TYPE_CHECKING, Dict, List, Optional

from django.contrib.auth import get_user_model

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

    def _update_fieldset_rulesets(
        self,
        fieldset: 'FieldSet',
        version: int,
        rulesets_data: Optional[List[Dict]] = None,
    ):

        # Absent key = snapshot predates rulesets, keep as-is.
        # Empty list = no rulesets, delete all.
        if rulesets_data is None:
            return
        api_names = set()
        for ruleset_data in rulesets_data:
            service = FieldSetRuleSetVersionService(
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
            )
            service.update_from_version(
                data=ruleset_data,
                version=version,
                fieldset=fieldset,
            )
            api_names.add(ruleset_data['api_name'])
        fieldset.rulesets.exclude(api_name__in=api_names).delete()

    def _update_field_rulesets(
        self,
        field: 'TaskField',
        rulesets_data: Optional[List[Dict]],
        version: int,
    ):

        if rulesets_data is None:
            return
        api_names = set()
        for ruleset_data in rulesets_data:
            service = FieldRuleSetVersionService(
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
            )
            service.update_from_version(
                data=ruleset_data,
                version=version,
                field=field,
            )
            api_names.add(ruleset_data['api_name'])
        field.rulesets.exclude(api_name__in=api_names).delete()


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
