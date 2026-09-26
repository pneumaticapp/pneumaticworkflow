import logging
from typing import Dict, List, Optional

from django.db.models import Q

from src.processes.enums import (
    FieldRuleOperator,
    FieldRuleType,
    FieldType,
    PredicateOperator,
)
from src.processes.models.workflows.fields import (
    FieldRuleGroupAnd,
    FieldRuleSet,
    TaskField,
)
from src.processes.services.tasks.fields.resolvers import (
    CheckboxFieldResolver,
    DateFieldResolver,
    DropdownFieldResolver,
    FieldRuleResolver,
    FileFieldResolver,
    GroupFieldResolver,
    NumberFieldResolver,
    StringFieldResolver,
    UserFieldResolver,
)

logger = logging.getLogger(__name__)


OPERATOR_MAP = {
    FieldRuleOperator.EQUAL: PredicateOperator.EQUAL,
    FieldRuleOperator.GREATER_THAN: (
        PredicateOperator.MORE_THAN
    ),
}

# FieldType does not define GROUP; the string matches
# PredicateType.GROUP used by condition_check.
_GROUP = 'group'


class FieldRuleSetCheckService:

    """ Evaluates field-level show/validator rulesets at
        runtime.

        Structured like ConditionCheckService: dispatches
        per-type evaluation to FieldRuleResolver subclasses
        via RESOLVERS map.  Does not depend on condition
        models (Predicate, Rule, Condition). """

    RESOLVERS: Dict[str, type] = {
        FieldType.NUMBER: NumberFieldResolver,
        FieldType.STRING: StringFieldResolver,
        FieldType.TEXT: StringFieldResolver,
        FieldType.URL: StringFieldResolver,
        FieldType.FILE: FileFieldResolver,
        FieldType.DROPDOWN: DropdownFieldResolver,
        FieldType.RADIO: DropdownFieldResolver,
        FieldType.CHECKBOX: CheckboxFieldResolver,
        FieldType.USER: UserFieldResolver,
        FieldType.DATE: DateFieldResolver,
        _GROUP: GroupFieldResolver,
    }

    @classmethod
    def check(
        cls,
        ruleset: FieldRuleSet,
        source_fields: Dict[str, TaskField],
    ) -> bool:

        """ True when at least one OR-branch passes (all
            its AND-conditions are true). """

        for group_or in ruleset.groups_or.all():
            groups_and = list(group_or.groups_and.all())
            if not groups_and:
                continue
            if all(
                cls._check_group_and(
                    group_and=group_and,
                    source_fields=source_fields,
                )
                for group_and in groups_and
            ):
                return True
        return False

    @classmethod
    def _check_group_and(
        cls,
        group_and: FieldRuleGroupAnd,
        source_fields: Dict[str, TaskField],
    ) -> bool:

        source = source_fields.get(group_and.field)
        if source is None:
            return False
        operator = OPERATOR_MAP.get(
            group_and.operator,
            group_and.operator,
        )
        return cls._evaluate(
            source=source,
            operator=operator,
            value=group_and.value,
        )

    @classmethod
    def _evaluate(
        cls,
        source: TaskField,
        operator: str,
        value: Optional[str],
    ) -> bool:

        resolver_cls = cls.RESOLVERS.get(
            source.type, StringFieldResolver,
        )
        try:
            resolver = resolver_cls(
                source, operator, value,
            )
            return resolver.resolve()
        except (
            ValueError, TypeError, ArithmeticError,
        ):
            return False

    @classmethod
    def _get_source_fields(
        cls,
        rulesets_by_field: Dict[
            int, List[FieldRuleSet]
        ],
        workflow_id: int,
    ) -> Dict[str, TaskField]:

        """ A show rule usually reads a kickoff field, so
            the source is looked up across the whole workflow
            and not among the fields being recalculated. """

        api_names = {
            group_and.field
            for rulesets in rulesets_by_field.values()
            for ruleset in rulesets
            for group_or in ruleset.groups_or.all()
            for group_and in group_or.groups_and.all()
            if group_and.field
        }
        if not api_names:
            return {}
        return {
            field.api_name: field
            for field in TaskField.objects.filter(
                workflow_id=workflow_id,
                api_name__in=api_names,
            )
        }

    @classmethod
    def apply_show_rulesets(
        cls,
        fields: List[TaskField],
        workflow_id: int,
    ):

        """ A field with show rulesets stays visible while
            at least one of them passes. Fields without show
            rulesets are left as they are. """

        if not fields:
            return
        rulesets_by_field: Dict[
            int, List[FieldRuleSet]
        ] = {}
        show_rulesets = (
            FieldRuleSet.objects
            .filter(
                field__in=fields,
                type=FieldRuleType.SHOW,
            )
            .prefetch_related('groups_or__groups_and')
        )
        for ruleset in show_rulesets:
            rulesets_by_field.setdefault(
                ruleset.field_id, [],
            ).append(ruleset)
        if not rulesets_by_field:
            return

        source_fields = cls._get_source_fields(
            rulesets_by_field=rulesets_by_field,
            workflow_id=workflow_id,
        )
        changed = []
        for field in fields:
            rulesets = rulesets_by_field.get(field.id)
            if not rulesets:
                continue
            is_hidden = not any(
                cls.check(
                    ruleset=ruleset,
                    source_fields=source_fields,
                )
                for ruleset in rulesets
            )
            if field.is_hidden != is_hidden:
                field.is_hidden = is_hidden
                changed.append(field)
        if changed:
            TaskField.objects.bulk_update(
                changed, ['is_hidden'],
            )

    @classmethod
    def apply_show_rulesets_for_task(cls, task):

        """ Every field of the task, not only the ones just
            submitted: a field hidden by a show rule is not
            sent by the client, so filtering by the payload
            would never let it reappear.

            Fieldset fields carry no task FK, they are
            reached through the fieldset. """

        cls.apply_show_rulesets(
            list(
                TaskField.objects.filter(
                    Q(fieldset__task=task)
                    | Q(task=task),
                    rulesets__type=FieldRuleType.SHOW,
                ).distinct(),
            ),
            workflow_id=task.workflow_id,
        )

    @classmethod
    def apply_show_rulesets_for_workflow(
        cls, workflow,
    ):

        """ Every field of the workflow, including kickoff
            and kickoff-fieldset fields: a show target can
            sit on the kickoff (Note) and still read another
            kickoff field. """

        cls.apply_show_rulesets(
            list(
                TaskField.objects.filter(
                    workflow=workflow,
                    rulesets__type=FieldRuleType.SHOW,
                ).distinct(),
            ),
            workflow_id=workflow.id,
        )
