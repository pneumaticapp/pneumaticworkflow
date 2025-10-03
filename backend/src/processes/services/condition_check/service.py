from typing import List

from src.processes.models import Condition, Rule, Predicate
from src.processes.services.condition_check.resolvers import (
    DateResolver,
    StringResolver,
    UserResolver,
    GroupResolver,
    FileResolver,
    DropdownResolver,
    CheckboxResolver,
    TaskResolver,
    KickoffResolver,
    NumberResolver,
)
from src.processes.enums import PredicateType


class ConditionCheckService:

    RESOLVERS = {
        PredicateType.NUMBER: NumberResolver,
        PredicateType.STRING: StringResolver,
        PredicateType.TEXT: StringResolver,
        PredicateType.URL: StringResolver,
        PredicateType.FILE: FileResolver,
        PredicateType.DROPDOWN: DropdownResolver,
        PredicateType.RADIO: DropdownResolver,
        PredicateType.CHECKBOX: CheckboxResolver,
        PredicateType.USER: UserResolver,
        PredicateType.GROUP: GroupResolver,
        PredicateType.DATE: DateResolver,
        PredicateType.TASK: TaskResolver,
        PredicateType.KICKOFF: KickoffResolver,
    }

    @classmethod
    def _check_predicate(cls, predicate: Predicate, workflow_id: int) -> bool:
        resolver = cls.RESOLVERS[predicate.field_type](predicate, workflow_id)
        return resolver.resolve()

    @classmethod
    def _check_predicates(
        cls,
        predicates: List[Predicate],
        workflow_id: int,
    ) -> bool:
        for predicate in predicates:
            if not cls._check_predicate(predicate, workflow_id):
                return False
        return True

    @classmethod
    def _check_rules(cls, rules: List[Rule], workflow_id: int) -> bool:
        for rule in rules:
            predicates = rule.predicates.all()
            if cls._check_predicates(predicates, workflow_id):
                return True
        return False

    @classmethod
    def check(cls, condition: Condition, workflow_id: int) -> bool:
        rules = condition.rules.all()
        return cls._check_rules(rules, workflow_id)
