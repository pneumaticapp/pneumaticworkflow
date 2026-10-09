import contextlib
from datetime import datetime
from datetime import timezone as tz
from decimal import Decimal, InvalidOperation
from typing import (
    Any,
    Dict,
    Iterable,
    Optional,
    Tuple,
)

from src.processes.enums import (
    FieldRuleOperator,
    FieldRuleType,
    FieldType,
)
from src.processes.messages.workflow import (
    MSG_PW_0092,
)
from src.processes.models.workflows.fields import (
    FieldRuleGroupAnd,
    FieldRuleGroupOr,
    FieldRuleSet,
    TaskField,
)
from src.processes.services.exceptions import (
    FieldRuleCheckServiceException,
)


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    with contextlib.suppress(ValueError, TypeError, OSError):
        return datetime.fromtimestamp(float(value), tz=tz.utc)
    return None


class FieldRuleOperations:

    """ Isolated comparison operations for field rulesets. """

    @classmethod
    def equal(cls, field_value: Any, rule_value: Any) -> bool:
        return field_value == rule_value

    @classmethod
    def not_equal(cls, field_value: Any, rule_value: Any) -> bool:
        return not cls.equal(field_value, rule_value)

    @classmethod
    def greater_than(cls, field_value: Any, rule_value: Any) -> bool:
        if field_value is None or rule_value is None:
            return False
        try:
            return field_value > rule_value
        except TypeError:
            return False

    @classmethod
    def less_than(cls, field_value: Any, rule_value: Any) -> bool:
        if field_value is None or rule_value is None:
            return False
        try:
            return field_value < rule_value
        except TypeError:
            return False

    @classmethod
    def exists(cls, field_value: Any) -> bool:
        if field_value is None:
            return False
        if field_value == 0:
            return True
        return bool(field_value)

    @classmethod
    def not_exists(cls, field_value: Any) -> bool:
        return not cls.exists(field_value)

    @classmethod
    def contains(cls, container: Optional[Any], item: Any) -> bool:
        if container is None or item is None:
            return False
        if isinstance(item, str) and not item:
            return False
        try:
            return item in container
        except TypeError:
            return False

    @classmethod
    def not_contains(cls, container: Optional[Any], item: Any) -> bool:
        if container is None or item is None:
            return False
        if isinstance(item, str) and not item:
            return False
        return not cls.contains(container, item)


class FieldRuleCheckService:

    """ Evaluates field-level show and validator rulesets at runtime. """

    OPERATOR_MAP = {
        FieldRuleOperator.EQUAL: FieldRuleOperations.equal,
        FieldRuleOperator.NOT_EQUAL: FieldRuleOperations.not_equal,
        FieldRuleOperator.GREATER_THAN: FieldRuleOperations.greater_than,
        FieldRuleOperator.LESS_THAN: FieldRuleOperations.less_than,
        FieldRuleOperator.EXIST: FieldRuleOperations.exists,
        FieldRuleOperator.NOT_EXIST: FieldRuleOperations.not_exists,
        FieldRuleOperator.CONTAIN: FieldRuleOperations.contains,
        FieldRuleOperator.NOT_CONTAIN: FieldRuleOperations.not_contains,
    }

    UNARY_OPERATORS = {
        FieldRuleOperator.EXIST,
        FieldRuleOperator.NOT_EXIST,
    }

    EQUALITY_OPERATORS = {
        FieldRuleOperator.EQUAL,
        FieldRuleOperator.NOT_EQUAL,
    }

    def __init__(self, workflow_id: int):
        self.workflow_id = workflow_id
        self._source_fields: Optional[Dict[str, TaskField]] = None
        self._show_results: Dict[str, Tuple[TaskField, bool]] = {}

    @property
    def source_fields(self) -> Dict[str, TaskField]:
        if self._source_fields is None:
            self._source_fields = self._get_source_fields(self.workflow_id)
        return self._source_fields

    def _get_source_fields(self, workflow_id: int) -> Dict[str, TaskField]:

        """ Load all workflow fields (kickoff + tasks) in 1 SQL query. """

        return {
            field.api_name: field
            for field in TaskField.objects.filter(
                workflow_id=workflow_id,
                is_deleted=False,
            ).prefetch_related('storage_attachments')
        }

    def _prepare_values(
        self,
        source: TaskField,
        operator: str,
        raw_value: Optional[str],
    ) -> tuple:
        if source.type == FieldType.NUMBER:
            try:
                field_val = (
                    Decimal(source.value)
                    if source.value is not None and source.value != ''
                    else None
                )
            except (InvalidOperation, TypeError, ValueError):
                field_val = None
            try:
                rule_val = (
                    Decimal(raw_value)
                    if raw_value is not None and raw_value != ''
                    else None
                )
            except (InvalidOperation, TypeError, ValueError):
                rule_val = None
            return field_val, rule_val

        if source.type == FieldType.DATE:
            return _parse_date(source.value), _parse_date(raw_value)

        if source.type == FieldType.CHECKBOX:
            field_val = {
                v.strip() for v in source.value.split(',') if v.strip()
            } if source.value else set()
            if operator in self.EQUALITY_OPERATORS:
                rule_val = {
                    v.strip() for v in raw_value.split(',') if v.strip()
                } if raw_value else set()
            elif operator in self.UNARY_OPERATORS:
                rule_val = None
            else:
                rule_val = (
                    raw_value.strip()
                    if isinstance(raw_value, str)
                    else raw_value
                )
            return field_val, rule_val

        if source.type == FieldType.USER:
            field_val = source.user_id or source.group_id or None
            if operator in self.UNARY_OPERATORS:
                return field_val, None
            try:
                rule_val = int(raw_value) if raw_value else None
            except (ValueError, TypeError):
                rule_val = None
            return field_val, rule_val

        if source.type == FieldType.FILE:
            has_files = bool(source.storage_attachments.all())
            field_val = True if has_files else None
            return field_val, None

        if source.type in {
            FieldType.STRING,
            FieldType.TEXT,
            FieldType.URL,
        }:
            if operator in self.UNARY_OPERATORS:
                return (source.value or None), None
            field_val = source.value or ''
            rule_val = raw_value or ''
            return field_val, rule_val

        field_val = source.value or None
        rule_val = raw_value
        return field_val, rule_val

    def _check_predicate(
        self,
        predicate: FieldRuleGroupAnd,
        ruleset: Optional[FieldRuleSet] = None,
    ) -> bool:
        if predicate.field:
            source = self.source_fields.get(predicate.field)
        elif ruleset and ruleset.field:
            source = self.source_fields.get(
                ruleset.field.api_name,
                ruleset.field,
            )
        else:
            source = None

        if source is None:
            return False

        op_func = self.OPERATOR_MAP.get(predicate.operator)
        if op_func is None:
            return False

        field_val, rule_val = self._prepare_values(
            source=source,
            operator=predicate.operator,
            raw_value=predicate.value,
        )
        if predicate.operator in self.UNARY_OPERATORS:
            return op_func(field_val)
        return op_func(field_val, rule_val)

    def _check_group_or(
        self,
        group_or: FieldRuleGroupOr,
        ruleset: Optional[FieldRuleSet] = None,
    ) -> bool:
        groups_and = list(group_or.groups_and.all())
        if not groups_and:
            return False
        return all(
            self._check_predicate(predicate, ruleset=ruleset)
            for predicate in groups_and
        )

    def _check_ruleset_condition(
        self,
        ruleset: FieldRuleSet,
    ) -> bool:
        groups_or = list(ruleset.groups_or.all())
        if not groups_or:
            return False
        return any(
            self._check_group_or(group_or, ruleset=ruleset)
            for group_or in groups_or
        )

    def _get_field(self, ruleset: FieldRuleSet) -> TaskField:
        return self.source_fields.get(
            ruleset.field.api_name,
            ruleset.field,
        )

    def _apply_show(self, ruleset: FieldRuleSet):
        field = self._get_field(ruleset)
        is_satisfied = self._check_ruleset_condition(ruleset)
        _, is_shown = self._show_results.get(field.api_name, (field, False))
        self._show_results[field.api_name] = (field, is_shown or is_satisfied)

    def _apply_validator(self, ruleset: FieldRuleSet):
        field = self._get_field(ruleset)
        if field.is_hidden:
            return
        is_satisfied = self._check_ruleset_condition(ruleset)
        if not is_satisfied:
            raise FieldRuleCheckServiceException(
                field_api_name=field.api_name,
                message=ruleset.message or MSG_PW_0092,
            )

    def apply_ruleset(self, ruleset: FieldRuleSet):
        apply_method = getattr(self, f'_apply_{ruleset.type}')
        apply_method(ruleset)

    def apply_rulesets(self, rulesets: Iterable[FieldRuleSet]):

        """ Show rulesets go first: a field stays visible while at least
            one of its show rulesets passes, and validators skip hidden
            fields. """

        rulesets = list(rulesets)
        self._show_results = {}
        for ruleset in rulesets:
            if ruleset.type == FieldRuleType.SHOW:
                self.apply_ruleset(ruleset)

        fields_to_update = []
        for field, is_shown in self._show_results.values():
            if field.is_hidden == is_shown:
                field.is_hidden = not is_shown
                fields_to_update.append(field)
        if fields_to_update:
            TaskField.objects.bulk_update(fields_to_update, ['is_hidden'])

        for ruleset in rulesets:
            if ruleset.type == FieldRuleType.VALIDATOR:
                self.apply_ruleset(ruleset)
