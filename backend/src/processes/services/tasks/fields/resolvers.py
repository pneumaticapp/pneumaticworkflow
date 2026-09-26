import contextlib
from datetime import datetime
from datetime import timezone as tz
from decimal import Decimal
from typing import Optional

from src.processes.enums import PredicateOperator
from src.processes.models.workflows.fields import TaskField
from src.processes.services.condition_check.comparator import (
    Comparator,
)


def _parse_date(value):
    if isinstance(value, str):
        with contextlib.suppress(ValueError):
            value = int(value)
    if isinstance(value, int):
        try:
            return datetime.fromtimestamp(value, tz=tz.utc)
        except (ValueError, TypeError):
            pass
    return None


class FieldRuleResolver:

    """ Base resolver for field rule evaluation.

        Mirrors condition_check/resolvers/base.py Resolver but
        receives an already-resolved source field instead of
        doing its own DB lookup. """

    field_value = None
    predicate_value = None

    def __init__(
        self,
        source: TaskField,
        operator: str,
        value: Optional[str],
    ):
        self._source = source
        self._operator = operator
        self._value = value
        self._prepare_args()

    def _prepare_args(self):
        raise NotImplementedError

    def resolve(self) -> bool:
        method = getattr(
            Comparator, self._operator, None,
        )
        if method is None:
            return False
        if self._operator in (
            PredicateOperator.UNARY_OPERATORS
        ):
            return method(self.field_value)
        return method(self.field_value, self.predicate_value)


class NumberFieldResolver(FieldRuleResolver):
    def _prepare_args(self):
        self.field_value = (
            Decimal(self._source.value)
            if self._source.value
            else None
        )
        self.predicate_value = (
            Decimal(self._value)
            if self._value
            else None
        )


class StringFieldResolver(FieldRuleResolver):
    def _prepare_args(self):
        self.field_value = self._source.value or None
        self.predicate_value = self._value


class DateFieldResolver(FieldRuleResolver):
    def _prepare_args(self):
        self.field_value = _parse_date(
            self._source.value,
        )
        self.predicate_value = _parse_date(self._value)


class CheckboxFieldResolver(FieldRuleResolver):
    def _prepare_args(self):
        self.field_value = (
            self._source.value.split(',')
            if self._source.value
            else []
        )
        if self._operator in {
            PredicateOperator.EQUAL,
            PredicateOperator.NOT_EQUAL,
        }:
            self.predicate_value = [self._value]
        else:
            self.predicate_value = self._value


class DropdownFieldResolver(FieldRuleResolver):
    def _prepare_args(self):
        self.field_value = self._source.value or None
        self.predicate_value = self._value


class UserFieldResolver(FieldRuleResolver):
    def _prepare_args(self):
        self.field_value = self._source.user_id or None
        self.predicate_value = (
            int(self._value) if self._value else None
        )


class GroupFieldResolver(FieldRuleResolver):
    def _prepare_args(self):
        self.field_value = (
            self._source.group_id or None
        )
        self.predicate_value = (
            int(self._value) if self._value else None
        )


class FileFieldResolver(FieldRuleResolver):
    def _prepare_args(self):
        has_files = (
            self._source.storage_attachments.exists()
        )
        self.field_value = True if has_files else None
