from typing import List
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.models import (
    Rule,
    Predicate,
)

UserModel = get_user_model()


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
        rules_tree: dict
    ):

        # TODO Move to PredicateService

        predicates = []
        for rule in rules:
            predicates_by_rule = rules_tree[rule.api_name]
            for predicate in predicates_by_rule:
                predicate.rule = rule
                predicates.append(predicate)
        Predicate.objects.bulk_create(predicates)
