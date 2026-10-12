from typing import Dict, List

from django.contrib.auth import get_user_model
from django.db.models import Q

from src.generics.base.service import BaseModelService
from src.processes.enums import (
    FieldRuleOperator,
    FieldRuleType,
    PredicateOperator,
)
from src.processes.models.templates.fields import FieldTemplateRuleSet
from src.processes.models.workflows.conditions import Predicate
from src.processes.models.workflows.fields import (
    FieldRuleGroupAnd,
    FieldRuleGroupOr,
    FieldRuleSet,
    TaskField,
)
from src.processes.services.base import BaseUpdateVersionService
from src.processes.services.condition_check.service import (
    ConditionCheckService,
)

UserModel = get_user_model()


class FieldRuleSetService(BaseModelService):

    """ Runtime counterpart of FieldTemplateRuleSetService.

        Field rulesets describe the same kind of condition as task
        conditions, so evaluation reuses the condition resolvers. Only
        two operator names differ between the two vocabularies. """

    COMPARATOR_OPERATORS = {
        FieldRuleOperator.EQUAL: PredicateOperator.EQUAL,
        FieldRuleOperator.GREATER_THAN: PredicateOperator.MORE_THAN,
    }

    def _create_instance(
        self,
        instance_template: FieldTemplateRuleSet,
        field: TaskField,
        **kwargs,
    ) -> FieldRuleSet:

        self.instance = FieldRuleSet.objects.create(
            account=self.account,
            workflow_id=field.workflow_id,
            field=field,
            api_name=instance_template.api_name,
            name=instance_template.name,
            type=instance_template.type,
            message=instance_template.message,
            order=instance_template.order,
        )
        return self.instance

    def _create_related(
        self,
        instance_template: FieldTemplateRuleSet,
        **kwargs,
    ):
        self._create_groups_or(instance_template=instance_template)

    def _create_groups_or(self, instance_template: FieldTemplateRuleSet):
        for group_or_template in instance_template.groups_or.all():
            group_or = FieldRuleGroupOr.objects.create(
                account=self.account,
                workflow_id=self.instance.workflow_id,
                ruleset=self.instance,
                api_name=group_or_template.api_name,
            )
            for group_and_template in group_or_template.groups_and.all():
                FieldRuleGroupAnd.objects.create(
                    account=self.account,
                    workflow_id=self.instance.workflow_id,
                    group_or=group_or,
                    api_name=group_and_template.api_name,
                    field=group_and_template.field,
                    operator=group_and_template.operator,
                    value=group_and_template.value,
                )

    @classmethod
    def _check_group_and(
        cls,
        group_and: FieldRuleGroupAnd,
        source_fields: Dict[str, TaskField],
        workflow_id: int,
    ) -> bool:

        source = source_fields.get(group_and.field)
        if source is None:
            return False
        predicate = Predicate(
            field_type=source.type,
            field=group_and.field,
            operator=cls.COMPARATOR_OPERATORS.get(
                group_and.operator,
                group_and.operator,
            ),
            value=group_and.value,
        )
        return ConditionCheckService.check_predicate(
            predicate,
            workflow_id,
            field=source,
        )

    @classmethod
    def _check_ruleset(
        cls,
        ruleset: FieldRuleSet,
        source_fields: Dict[str, TaskField],
    ) -> bool:

        for group_or in ruleset.groups_or.all():
            groups_and = list(group_or.groups_and.all())
            if not groups_and:
                continue
            if all(
                cls._check_group_and(
                    group_and=group_and,
                    source_fields=source_fields,
                    workflow_id=ruleset.workflow_id,
                )
                for group_and in groups_and
            ):
                return True
        return False

    @classmethod
    def _get_source_fields(
        cls,
        rulesets_by_field: Dict[int, List[FieldRuleSet]],
        workflow_id: int,
    ) -> Dict[str, TaskField]:

        """ A show rule usually reads a kickoff field, so the source is
            looked up across the whole workflow and not among the
            fields being recalculated. """

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
        workflow_id: int = None,
    ):

        """ A field with show rulesets stays visible while at least one
            of them passes. Fields without show rulesets are left as
            they are. """

        if not fields:
            return
        if workflow_id is None:
            raise TypeError('workflow_id is required')
        rulesets_by_field = {}
        show_rulesets = (
            FieldRuleSet.objects
            .filter(field__in=fields, type=FieldRuleType.SHOW)
            .prefetch_related('groups_or__groups_and')
        )
        for ruleset in show_rulesets:
            rulesets_by_field.setdefault(ruleset.field_id, []).append(ruleset)
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
                cls._check_ruleset(
                    ruleset=ruleset,
                    source_fields=source_fields,
                )
                for ruleset in rulesets
            )
            if field.is_hidden != is_hidden:
                field.is_hidden = is_hidden
                changed.append(field)
        if changed:
            TaskField.objects.bulk_update(changed, ['is_hidden'])

    @classmethod
    def apply_show_rulesets_for_task(cls, task):

        """ Every field of the task, not only the ones just submitted:
            a field hidden by a show rule is not sent by the client, so
            filtering by the payload would never let it reappear.

            Fieldset fields carry no task FK, they are reached through
            the fieldset — hence the two branches. """

        cls.apply_show_rulesets(
            list(
                TaskField.objects.filter(
                    Q(fieldset__task=task) | Q(task=task),
                    rulesets__type=FieldRuleType.SHOW,
                ).distinct(),
            ),
            workflow_id=task.workflow_id,
        )

    @classmethod
    def apply_show_rulesets_for_workflow(cls, workflow):

        """ Every field of the workflow, including kickoff and
            kickoff-fieldset fields: a show target can sit on the
            kickoff (Note) and still read another kickoff field. """

        cls.apply_show_rulesets(
            list(
                TaskField.objects.filter(
                    workflow=workflow,
                    rulesets__type=FieldRuleType.SHOW,
                ).distinct(),
            ),
            workflow_id=workflow.id,
        )


class FieldRuleSetVersionService(BaseUpdateVersionService):

    """ Version update reads a snapshot, so it works with dicts while
        FieldRuleSetService works with template objects. """

    def _update_groups_and(
        self,
        group_or: FieldRuleGroupOr,
        groups_and_data: List[Dict],
    ):
        api_names = set()
        for group_and_data in groups_and_data:
            FieldRuleGroupAnd.objects.update_or_create(
                group_or=group_or,
                api_name=group_and_data['api_name'],
                defaults={
                    'account_id': group_or.account_id,
                    'workflow_id': group_or.workflow_id,
                    'field': group_and_data.get('field'),
                    'operator': group_and_data['operator'],
                    'value': group_and_data.get('value'),
                },
            )
            api_names.add(group_and_data['api_name'])
        group_or.groups_and.exclude(api_name__in=api_names).delete()

    def _update_groups_or(self, groups_or_data: List[Dict]):
        api_names = set()
        for group_or_data in groups_or_data:
            group_or, _ = FieldRuleGroupOr.objects.update_or_create(
                ruleset=self.instance,
                api_name=group_or_data['api_name'],
                defaults={
                    'account_id': self.instance.account_id,
                    'workflow_id': self.instance.workflow_id,
                },
            )
            self._update_groups_and(
                group_or=group_or,
                groups_and_data=group_or_data.get('groups_and') or [],
            )
            api_names.add(group_or_data['api_name'])
        self.instance.groups_or.exclude(api_name__in=api_names).delete()

    def update_from_version(
        self,
        data: Dict,
        version: int,
        **kwargs,
    ) -> FieldRuleSet:

        field = kwargs['field']
        self.instance, _ = FieldRuleSet.objects.update_or_create(
            field=field,
            api_name=data['api_name'],
            defaults={
                'account_id': field.account_id,
                'workflow_id': field.workflow_id,
                'name': data.get('name', ''),
                'type': data['type'],
                'message': data.get('message'),
                'order': data.get('order', 0),
            },
        )
        self._update_groups_or(data.get('groups_or') or [])
        return self.instance
