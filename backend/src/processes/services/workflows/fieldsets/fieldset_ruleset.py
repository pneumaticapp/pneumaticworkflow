import contextlib
from decimal import Decimal, DecimalException
from typing import Dict, Iterable, List, Optional, Tuple, Union

from django.contrib.auth import get_user_model

from src.generics.base.service import BaseModelService
from src.processes.enums import FieldSetRuleOperator
from src.processes.messages.fieldset import (
    MSG_FS_0002,
    MSG_FS_0012,
)
from src.processes.models.templates.fieldset import (
    FieldSetTemplateRuleGroupAnd,
    FieldSetTemplateRuleGroupOr,
    FieldSetTemplateRuleSet,
)
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.fieldset import (
    FieldSet,
    FieldSetRuleGroupAnd,
    FieldSetRuleGroupOr,
    FieldSetRuleSet,
)
from src.processes.services.base import BaseUpdateVersionService
from src.processes.services.exceptions import FieldsetServiceException

UserModel = get_user_model()


class FieldSetRuleSetService(BaseModelService):

    NULL_VALUES = (None, '', [])

    def _create_instance(
        self,
        instance_template: Optional[FieldSetTemplateRuleSet] = None,
        fieldset: Optional[FieldSet] = None,
        **kwargs,
    ) -> FieldSetRuleSet:
        fieldset_id = (
            kwargs.get('fieldset_id') or getattr(fieldset, 'id', None)
        )
        workflow_id = (
            kwargs.get('workflow_id')
            or getattr(kwargs.get('workflow'), 'id', None)
            or getattr(fieldset, 'workflow_id', None)
        )
        account = (
            self.account
            or getattr(fieldset, 'account', None)
            or getattr(kwargs.get('workflow'), 'account', None)
            or kwargs.get('account')
        )
        api_name = kwargs.get('api_name') or getattr(
            instance_template, 'api_name', None,
        )
        create_kwargs = {
            'account': account,
            'workflow_id': workflow_id,
            'fieldset_id': fieldset_id,
            'message': kwargs.get('message', getattr(
                instance_template, 'message', None,
            )),
            'order': kwargs.get('order', getattr(
                instance_template, 'order', 0,
            )),
        }
        if api_name:
            create_kwargs['api_name'] = api_name

        self.instance = FieldSetRuleSet.objects.create(**create_kwargs)
        return self.instance

    def _set_fields(
        self,
        instance_template: Optional[FieldSetTemplateRuleSet] = None,
        fields_api_names: Optional[Iterable[str]] = None,
        **kwargs,
    ):
        if fields_api_names is None and instance_template:
            fields_api_names = [
                f.api_name for f in instance_template.fields.all()
                if not getattr(f, 'is_deleted', False)
            ]

        if fields_api_names:
            task_fields = TaskField.objects.filter(
                fieldset_id=self.instance.fieldset_id,
                api_name__in=fields_api_names,
            )
            self.instance.fields.set(task_fields)
        else:
            self.instance.fields.clear()

    def _build_group_and(
        self,
        group_or: FieldSetRuleGroupOr,
        data: Union[FieldSetTemplateRuleGroupAnd, Dict],
    ) -> FieldSetRuleGroupAnd:
        if isinstance(data, dict):
            api_name = data.get('api_name')
            operator = data['operator']
            value = data.get('value')
        else:
            api_name = data.api_name
            operator = data.operator
            value = data.value

        create_kwargs = {
            'account': self.instance.account,
            'workflow_id': self.instance.workflow_id,
            'group_or': group_or,
            'operator': operator,
            'value': value,
        }
        if api_name:
            create_kwargs['api_name'] = api_name

        return FieldSetRuleGroupAnd(**create_kwargs)

    def _create_group_or(
        self,
        data: Union[FieldSetTemplateRuleGroupOr, Dict],
    ) -> FieldSetRuleGroupOr:
        if isinstance(data, dict):
            api_name = data.get('api_name')
            groups_and_data = data.get('groups_and', [])
        else:
            api_name = data.api_name
            groups_and_data = [
                a for a in data.groups_and.all()
                if not getattr(a, 'is_deleted', False)
            ]

        create_kwargs = {
            'account': self.instance.account,
            'workflow_id': self.instance.workflow_id,
            'fieldset_rule': self.instance,
        }
        if api_name:
            create_kwargs['api_name'] = api_name

        group_or = FieldSetRuleGroupOr.objects.create(**create_kwargs)
        and_objects = [
            self._build_group_and(group_or=group_or, data=and_item)
            for and_item in groups_and_data
        ]
        if and_objects:
            FieldSetRuleGroupAnd.objects.bulk_create(and_objects)
        return group_or

    def _create_related(
        self,
        instance_template: Optional[FieldSetTemplateRuleSet] = None,
        groups_or: Optional[List] = None,
        **kwargs,
    ):
        fields_api_names = kwargs.get('fields')
        self._set_fields(
            instance_template=instance_template,
            fields_api_names=fields_api_names,
            **kwargs,
        )

        if groups_or is None and instance_template:
            groups_or = [
                g for g in instance_template.groups_or.all()
                if not getattr(g, 'is_deleted', False)
            ]

        if groups_or:
            for group_or_item in groups_or:
                self._create_group_or(data=group_or_item)

    def _create_actions(self, **kwargs):
        if kwargs.get('skip_validation') is False:
            self.validate(**kwargs)

    def _get_fields_sum(self) -> Tuple[Decimal, bool]:
        total = Decimal(0)
        values_exists = False
        for field in self.instance.fields.all():
            if field.value in self.NULL_VALUES:
                if field.is_required:
                    values_exists = True
            else:
                with contextlib.suppress(
                    ValueError, TypeError, DecimalException,
                ):
                    total += Decimal(field.value)
                values_exists = True
        return total, values_exists

    def _check_and_predicate(
        self,
        group_and: FieldSetRuleGroupAnd,
        total: Decimal,
    ) -> bool:
        try:
            target_value = Decimal(group_and.value)
        except (ValueError, TypeError, DecimalException):
            return False

        if group_and.operator == FieldSetRuleOperator.SUM_EQUAL:
            return total == target_value
        if group_and.operator == FieldSetRuleOperator.SUM_GREATER_THAN:
            return total > target_value
        if group_and.operator == FieldSetRuleOperator.SUM_LESS_THAN:
            return total < target_value
        return False

    def _get_error_message(
        self,
        all_ands: List[FieldSetRuleGroupAnd],
    ) -> str:
        if self.instance.message:
            return self.instance.message
        if len(all_ands) == 1:
            return MSG_FS_0002(all_ands[0].value)
        values_str = ', '.join(str(item.value) for item in all_ands)
        return MSG_FS_0012(values_str)

    def validate(self, **kwargs) -> bool:
        """Call after objects save. Checks OR-logic across groups_or,
        and AND-logic across groups_and within each group_or."""
        groups_or = list(self.instance.groups_or.all())
        if not groups_or:
            return True

        total, values_exists = self._get_fields_sum()
        if not values_exists:
            return True

        for group_or in groups_or:
            groups_and = list(group_or.groups_and.all())
            if not groups_and:
                continue
            if all(
                self._check_and_predicate(and_item, total)
                for and_item in groups_and
            ):
                return True

        all_ands = [
            and_item
            for group_or in groups_or
            for and_item in group_or.groups_and.all()
        ]
        if not all_ands:
            return True

        raise FieldsetServiceException(
            message=self._get_error_message(all_ands),
        )


class FieldSetRuleSetVersionService(BaseUpdateVersionService):

    """ Version update reads a snapshot, so it works with dicts while
        FieldSetRuleSetService works with template objects. Same split
        as ChecklistService and ChecklistUpdateVersionService. """

    def _set_fields(self, api_names: List[str]):
        if not api_names:
            self.instance.fields.clear()
            return
        self.instance.fields.set(
            TaskField.objects.filter(
                fieldset_id=self.instance.fieldset_id,
                api_name__in=api_names,
            ),
        )

    def _update_groups_and(
        self,
        group_or: FieldSetRuleGroupOr,
        groups_and_data: List[Dict],
    ):
        api_names = set()
        for group_and_data in groups_and_data:
            FieldSetRuleGroupAnd.objects.update_or_create(
                group_or=group_or,
                api_name=group_and_data['api_name'],
                defaults={
                    'account_id': group_or.account_id,
                    'workflow_id': group_or.workflow_id,
                    'operator': group_and_data['operator'],
                    'value': group_and_data.get('value'),
                },
            )
            api_names.add(group_and_data['api_name'])
        group_or.groups_and.exclude(api_name__in=api_names).delete()

    def _update_groups_or(self, groups_or_data: List[Dict]):
        api_names = set()
        for group_or_data in groups_or_data:
            group_or, _ = FieldSetRuleGroupOr.objects.update_or_create(
                fieldset_rule=self.instance,
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
    ) -> FieldSetRuleSet:

        """ Call after the fieldset fields are updated: the fields m2m
            resolves api_names to rows that must already exist. """

        fieldset = kwargs['fieldset']
        self.instance, _ = FieldSetRuleSet.objects.update_or_create(
            fieldset=fieldset,
            api_name=data['api_name'],
            defaults={
                'account_id': fieldset.account_id,
                'workflow_id': fieldset.workflow_id,
                'message': data.get('message'),
                'order': data.get('order', 0),
            },
        )
        self._update_groups_or(data.get('groups_or') or [])
        self._set_fields(data.get('fields') or [])
        return self.instance
