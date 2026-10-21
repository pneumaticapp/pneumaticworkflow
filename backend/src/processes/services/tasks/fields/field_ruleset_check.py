from datetime import date
from decimal import Decimal, InvalidOperation
from typing import (
    Any,
    Dict,
    Iterable,
    Optional,
    Set,
    Tuple,
)

from src.processes.enums import (
    FieldRuleOperator,
    FieldRuleValueType,
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

    def _decimal_or_none(self, raw: Optional[str]) -> Optional[Decimal]:
        try:
            if raw is None or raw == '':
                return None
            return Decimal(raw)
        except (InvalidOperation, TypeError, ValueError):
            # Stored value is not a decimal. The predicate fails.
            return None

    def _get_number_value(
        self,
        source: TaskField,
        operator: str,
        raw_value: Optional[str],
    ) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        return (
            self._decimal_or_none(source.value),
            self._decimal_or_none(raw_value),
        )

    def _get_date_value(
        self,
        source: TaskField,
        operator: str,
        raw_value: Optional[str],
    ) -> Tuple[Optional[date], Optional[date]]:
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

    def _get_checkbox_value(
        self,
        source: TaskField,
        operator: str,
        raw_value: Optional[str],
    ) -> Tuple[Set[str], Optional[Any]]:
        if source.value:
            field_val = {
                item.strip()
                for item in source.value.split(',')
                if item.strip()
            }
        else:
            field_val = set()
        if operator in self.EQUALITY_OPERATORS:
            if raw_value:
                rule_val = {
                    item.strip()
                    for item in raw_value.split(',')
                    if item.strip()
                }
            else:
                rule_val = set()
        elif operator in self.UNARY_OPERATORS:
            rule_val = None
        elif isinstance(raw_value, str):
            rule_val = raw_value.strip()
        else:
            rule_val = raw_value
        return field_val, rule_val

    def _get_string_value(
        self,
        source: TaskField,
        operator: str,
        raw_value: Optional[str],
    ) -> Tuple[Optional[str], Optional[str]]:
        if operator in self.UNARY_OPERATORS:
            return (source.value or None), None
        return (source.value or ''), (raw_value or '')

    def _get_user_field_value(self, source: TaskField) -> Optional[int]:
        return source.user_id or None

    def _get_group_field_value(self, source: TaskField) -> Optional[int]:
        return source.group_id or None

    def _get_user_value(
        self,
        source: TaskField,
        operator: str,
        raw_value: Optional[str],
        value_type: Optional[str] = None,
    ) -> Tuple[Optional[int], Optional[int]]:
        if value_type == FieldRuleValueType.GROUP:
            field_val = self._get_group_field_value(source)
        elif value_type == FieldRuleValueType.USER:
            field_val = self._get_user_field_value(source)
        else:
            field_val = (
                self._get_user_field_value(source)
                or self._get_group_field_value(source)
            )
        if operator in self.UNARY_OPERATORS:
            return field_val, None
        try:
            rule_val = int(raw_value) if raw_value else None
        except (ValueError, TypeError):
            rule_val = None
        return field_val, rule_val

    def _get_file_value(
        self,
        source: TaskField,
        operator: str,
        raw_value: Optional[str],
    ) -> Tuple[Optional[bool], None]:
        has_files = bool(source.storage_attachments.all())
        field_val = True if has_files else None
        return field_val, None

    def _get_selection_value(
        self,
        source: TaskField,
        operator: str,
        raw_value: Optional[str],
    ) -> Tuple[Optional[str], Optional[str]]:
        return source.value or None, raw_value

    VALUE_GETTERS = {
        FieldType.NUMBER: _get_number_value,
        FieldType.DATE: _get_date_value,
        FieldType.CHECKBOX: _get_checkbox_value,
        FieldType.STRING: _get_string_value,
        FieldType.TEXT: _get_string_value,
        FieldType.URL: _get_string_value,
        FieldType.RADIO: _get_selection_value,
        FieldType.DROPDOWN: _get_selection_value,
        FieldType.FILE: _get_file_value,
    }

    def _prepare_values(
        self,
        source: TaskField,
        operator: str,
        raw_value: Optional[str],
        value_type: Optional[str] = None,
    ) -> Tuple[Any, Any]:
        if source.type == FieldType.USER:
            return self._get_user_value(
                source,
                operator,
                raw_value,
                value_type,
            )
        getter = self.VALUE_GETTERS.get(
            source.type,
            FieldRuleCheckService._get_selection_value,
        )
        return getter(self, source, operator, raw_value)

    def _check_group_and(
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
            value_type=predicate.value_type,
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
        return all(
            self._check_group_and(
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
            return True
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
