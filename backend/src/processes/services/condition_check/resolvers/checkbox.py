from src.processes.enums import (
    PredicateOperator,
)

from .base import Resolver


class CheckboxResolver(Resolver):
    def _prepare_args(self):
        field = self._get_field()
        self.field_value = field.value.split(',') if field.value else []
        if self._predicate.operator in {
            PredicateOperator.EQUAL,
            PredicateOperator.NOT_EQUAL,
        }:
            self.predicate_value = [self._predicate.value]
        else:
            self.predicate_value = self._predicate.value
