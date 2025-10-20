from typing import List

from src.processes.enums import PredicateType
from src.processes.models.workflows.conditions import (
    Condition,
    Predicate,
    Rule,
)
from src.processes.services.condition_check.resolvers.checkbox import (
    CheckboxResolver,
)
from src.processes.services.condition_check.resolvers.date import DateResolver
from src.processes.services.condition_check.resolvers.dropdown import (
    DropdownResolver,
)
from src.processes.services.condition_check.resolvers.file import (
    FileResolver,
)
from src.processes.services.condition_check.resolvers.kickoff import (
    KickoffResolver,
)
from src.processes.services.condition_check.resolvers.number import (
    NumberResolver,
)
from src.processes.services.condition_check.resolvers.string import (
    StringResolver,
)
from src.processes.services.condition_check.resolvers.task import TaskResolver
from src.processes.services.condition_check.resolvers.user import UserResolver


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
