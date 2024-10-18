from typing import List

from pneumatic_backend.processes.models import Condition, Rule, Predicate
from .resolvers import (
    DateResolver,
    StringResolver,
    UserResolver,
    FileResolver,
    DropdownResolver,
    CheckboxResolver,
)
from pneumatic_backend.processes.enums import FieldType


class ConditionCheckService:
    RESOLVERS = {
        FieldType.STRING: StringResolver,
        FieldType.TEXT: StringResolver,
        FieldType.URL: StringResolver,
        FieldType.FILE: FileResolver,
        FieldType.DROPDOWN: DropdownResolver,
        FieldType.RADIO: DropdownResolver,
        FieldType.CHECKBOX: CheckboxResolver,
        FieldType.USER: UserResolver,
        FieldType.DATE: DateResolver,
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
