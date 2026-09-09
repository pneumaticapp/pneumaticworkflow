from decimal import Decimal, DecimalException
from typing import Dict, List, Optional

from django.contrib.auth import get_user_model
from django.db import transaction

from src.generics.base.service import BaseModelService
from src.processes.enums import FieldSetRuleOperator
from src.processes.messages.fieldset import MSG_FS_0002, MSG_FS_0012
from src.processes.models.templates.fieldset import FieldSetTemplateRuleSet
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

    """ Runtime counterpart of FieldsetTemplateRuleSetService.

        Copies a template ruleset into a workflow and evaluates it
        against the values the user has entered. """

    NULL_VALUES = (None, '', [])

    def _create_instance(
        self,
        instance_template: FieldSetTemplateRuleSet,
        fieldset: FieldSet,
        **kwargs,
    ) -> FieldSetRuleSet:

        self.instance = FieldSetRuleSet.objects.create(
            account=self.account,
            workflow_id=fieldset.workflow_id,
            fieldset=fieldset,
            api_name=instance_template.api_name,
            message=instance_template.message,
            order=instance_template.order,
        )
        return self.instance

    def _create_related(
        self,
        instance_template: FieldSetTemplateRuleSet,
        **kwargs,
    ):
        self._set_fields(instance_template=instance_template)
        self._create_groups_or(instance_template=instance_template)

    def _set_fields(self, instance_template: FieldSetTemplateRuleSet):

        """ Runtime fields keep the api_name of their template """

        api_names = [
            field_template.api_name
            for field_template in instance_template.fields.all()
        ]
        if not api_names:
            self.instance.fields.clear()
            return
        self.instance.fields.set(
            TaskField.objects.filter(
                fieldset_id=self.instance.fieldset_id,
                api_name__in=api_names,
            ),
        )

    def _create_groups_or(self, instance_template: FieldSetTemplateRuleSet):
        for group_or_template in instance_template.groups_or.all():
            group_or = FieldSetRuleGroupOr.objects.create(
                account=self.account,
                workflow_id=self.instance.workflow_id,
                fieldset_rule=self.instance,
                api_name=group_or_template.api_name,
            )
            for group_and_template in group_or_template.groups_and.all():
                FieldSetRuleGroupAnd.objects.create(
                    account=self.account,
                    workflow_id=self.instance.workflow_id,
                    group_or=group_or,
                    api_name=group_and_template.api_name,
                    operator=group_and_template.operator,
                    value=group_and_template.value,
                )

    def _get_total(self) -> Optional[Decimal]:

        """ None means there is nothing to check yet: every field is
            blank and none of them is required. """

        total = Decimal(0)
        has_values = False
        for field in self.instance.fields.all():
            if field.value in self.NULL_VALUES:
                if field.is_required:
                    has_values = True
                continue
            try:
                total += Decimal(field.value)
            except (TypeError, ValueError, DecimalException):
                continue
            has_values = True
        return total if has_values else None

    def _check_group_and(
        self,
        group_and: FieldSetRuleGroupAnd,
        total: Decimal,
    ) -> bool:

        try:
            expected = Decimal(group_and.value)
        except (TypeError, ValueError, DecimalException):
            return False
        if group_and.operator == FieldSetRuleOperator.SUM_EQUAL:
            return total == expected
        if group_and.operator == FieldSetRuleOperator.SUM_GREATER_THAN:
            return total > expected
        if group_and.operator == FieldSetRuleOperator.SUM_LESS_THAN:
            return total < expected
        return False

    def _get_error_message(self, expected_values: List[str]) -> str:
        if self.instance.message:
            return self.instance.message
        if len(expected_values) == 1:
            return MSG_FS_0002(expected_values[0])
        return MSG_FS_0012(', '.join(expected_values))

    def validate(self, **kwargs) -> bool:

        """ Call after the fields are saved.

            Branches in groups_or are combined with OR, conditions
            inside a branch with AND. """

        groups_or = list(self.instance.groups_or.all())
        if not groups_or:
            return True
        total = self._get_total()
        if total is None:
            return True

        expected_values = []
        for group_or in groups_or:
            groups_and = list(group_or.groups_and.all())
            if not groups_and:
                continue
            if all(
                self._check_group_and(group_and=group_and, total=total)
                for group_and in groups_and
            ):
                return True
            expected_values.extend(
                str(group_and.value) for group_and in groups_and
            )
        if not expected_values:
            return True
        raise FieldsetServiceException(
            message=self._get_error_message(expected_values),
        )

    def create(self, **kwargs) -> FieldSetRuleSet:
        with transaction.atomic():
            self._create_instance(**kwargs)
            self._create_related(**kwargs)
            self._create_actions(**kwargs)
            if kwargs.get('skip_validation') is False:
                self.validate(**kwargs)
        return self.instance


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
