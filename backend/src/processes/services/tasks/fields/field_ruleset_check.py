from decimal import Decimal, InvalidOperation
from typing import (
    Any,
    Dict,
    Iterable,
    Optional,
)

from src.processes.enums import (
    FieldRuleOperator,
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
from src.utils.dates import calendar_date_from_tsp


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

    def __init__(self, field: TaskField):
        self.field = field
        self.account = field.account
        self.workflow = field.workflow

    def _get_source(
        self,
        group_and: FieldRuleGroupAnd,
        fields_by_api_name: Dict[str, TaskField],
    ) -> Optional[TaskField]:
        if group_and.field:
            return fields_by_api_name.get(group_and.field)
        return self.field

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
            return (
                calendar_date_from_tsp(
                    raw_value=source.value,
                    timezone_name=self._timezone_name,
                ),
                calendar_date_from_tsp(
                    raw_value=raw_value,
                    timezone_name=self._timezone_name,
                ),
            )

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
        fields_by_api_name: Dict[str, TaskField],
    ) -> bool:
        source = self._get_source(predicate, fields_by_api_name)
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
        fields_by_api_name: Dict[str, TaskField],
    ) -> bool:
        groups_and = list(group_or.groups_and.all())
        if not groups_and:
            return False
        return all(
            self._check_predicate(
                predicate,
                fields_by_api_name,
            )
            for predicate in groups_and
        )

    def _check_ruleset_condition(
        self,
        ruleset: FieldRuleSet,
        fields_by_api_name: Dict[str, TaskField],
    ) -> bool:
        groups_or = list(ruleset.groups_or.all())
        if not groups_or:
            return False
        return any(
            self._check_group_or(group_or, fields_by_api_name)
            for group_or in groups_or
        )

    def _apply_validator(
        self,
        ruleset: FieldRuleSet,
        fields_by_api_name: Dict[str, TaskField],
    ):
        is_satisfied = self._check_ruleset_condition(
            ruleset,
            fields_by_api_name,
        )
        if not is_satisfied:
            raise FieldRuleCheckServiceException(
                field_api_name=self.field.api_name,
                message=ruleset.message or MSG_PW_0092,
            )

    def apply_rulesets(
        self,
        rulesets: Iterable[FieldRuleSet],
        timezone_name: str,
        fields_by_api_name: Dict[str, TaskField],
    ):

        """ Show rulesets go first: a field stays visible while at least
            one of its show rulesets passes, and validators skip hidden
            fields. """

        rulesets = list(rulesets)
        self._timezone_name = timezone_name
        has_show = False
        is_shown = False
        for ruleset in rulesets:
            if not ruleset.type_show:
                continue
            has_show = True
            is_shown = is_shown or self._check_ruleset_condition(
                ruleset,
                fields_by_api_name,
            )
        if has_show and self.field.is_hidden == is_shown:
            self.field.is_hidden = not is_shown
        if self.field.is_hidden:
            return
        for ruleset in rulesets:
            if ruleset.type_validator:
                self._apply_validator(ruleset, fields_by_api_name)
