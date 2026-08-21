from decimal import Decimal, DecimalException
from typing import Dict, List, Optional

from django.contrib.auth import get_user_model
from django.db import transaction

from src.generics.base.service import BaseModelService
from src.processes.enums import (
    FieldSetRuleOperator,
    FieldType,
)
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.fieldset import (
    FieldSetTemplateRuleGroupAnd,
    FieldSetTemplateRuleGroupOr,
    FieldSetTemplateRuleSet,
)
from src.processes.services.exceptions import (
    FieldsetTemplateRuleSumMaxFieldsNotNumber,
    FieldsetTemplateRuleSumMaxInvalidValue,
)


UserModel = get_user_model()


class FieldsetTemplateRuleSetService(BaseModelService):

    def _validate_sum(
        self,
        group_and: FieldSetTemplateRuleGroupAnd,
    ) -> Decimal:

        value = group_and.value
        if not value:
            raise FieldsetTemplateRuleSumMaxInvalidValue
        try:
            result = Decimal(value)
        except (ValueError, TypeError, DecimalException) as ex:
            raise FieldsetTemplateRuleSumMaxInvalidValue from ex

        if self.instance.fields.exclude(type=FieldType.NUMBER).exists():
            raise FieldsetTemplateRuleSumMaxFieldsNotNumber
        return result

    def _validate(
        self,
        group_and: FieldSetTemplateRuleGroupAnd,
    ):

        if group_and.operator in FieldSetRuleOperator.SUM_OPERATORS:
            self._validate_sum(group_and=group_and)

    def _create_instance(
        self,
        fieldset_id: int,
        api_name: Optional[str] = None,
        message: Optional[str] = None,
        order: int = 0,
        template_id: Optional[int] = None,
        **kwargs,
    ):

        create_kwargs = {
            'account': self.account,
            'message': message,
            'order': order,
            'fieldset_id': fieldset_id,
            'template_id': template_id,
        }
        if api_name:
            create_kwargs['api_name'] = api_name
        self.instance = FieldSetTemplateRuleSet.objects.create(**create_kwargs)
        return self.instance

    def _create_related(
        self,
        **kwargs,
    ):
        fields = kwargs.pop('fields', None)
        groups_or = kwargs.pop('groups_or', None)
        if fields is not None:
            self._set_fields(fields_api_names=fields)
        if groups_or is not None:
            self._set_groups_or(groups_or_data=groups_or)

    def _get_valid_fields(
        self,
        fields_api_names: List[str],
        **kwargs,
    ) -> List[FieldTemplate]:

        return list(
            FieldTemplate.objects
            .filter(
                fieldset_id=self.instance.fieldset_id,
                api_name__in=fields_api_names,
            ),
        )

    def _set_fields(self, fields_api_names: List[str], **kwargs):
        if fields_api_names:
            fields = self._get_valid_fields(
                fields_api_names=fields_api_names,
                **kwargs,
            )
            self.instance.fields.set(fields)
        else:
            self.instance.fields.clear()

    def _create_group_and(
        self,
        group_or: FieldSetTemplateRuleGroupOr,
        group_and_data: Dict,
    ) -> FieldSetTemplateRuleGroupAnd:
        create_kwargs = {
            'group_or': group_or,
            'account': self.account,
            'template_id': self.instance.template_id,
            'operator': group_and_data['operator'],
            'value': group_and_data.get('value'),
        }
        api_name = group_and_data.get('api_name')
        if api_name:
            create_kwargs['api_name'] = api_name
        group_and = FieldSetTemplateRuleGroupAnd.objects.create(
            **create_kwargs,
        )
        self._validate(group_and=group_and)
        return group_and

    def _update_group_and(
        self,
        group_and: FieldSetTemplateRuleGroupAnd,
        group_and_data: Dict,
    ) -> FieldSetTemplateRuleGroupAnd:
        update_fields = []
        if 'operator' in group_and_data:
            group_and.operator = group_and_data['operator']
            update_fields.append('operator')
        if 'value' in group_and_data:
            group_and.value = group_and_data['value']
            update_fields.append('value')
        if update_fields:
            group_and.save(update_fields=update_fields)
        self._validate(group_and=group_and)
        return group_and

    def _set_groups_and(
        self,
        group_or: FieldSetTemplateRuleGroupOr,
        groups_and_data: List[Dict],
    ):
        existing_groups_and = {
            group_and.api_name: group_and
            for group_and in group_or.groups_and.all()
        }
        groups_and_api_names = set()
        for group_and_data in groups_and_data:
            group_and_data_dict = dict(group_and_data)
            api_name = group_and_data_dict.get('api_name')
            if api_name and api_name in existing_groups_and:
                group_and = self._update_group_and(
                    group_and=existing_groups_and[api_name],
                    group_and_data=group_and_data_dict,
                )
            else:
                group_and = self._create_group_and(
                    group_or=group_or,
                    group_and_data=group_and_data_dict,
                )
            groups_and_api_names.add(group_and.api_name)
        group_or.groups_and.exclude(
            api_name__in=groups_and_api_names,
        ).delete()

    def _create_group_or(
        self,
        group_or_data: Dict,
    ) -> FieldSetTemplateRuleGroupOr:
        group_or_data_dict = dict(group_or_data)
        groups_and_data = group_or_data_dict.pop('groups_and', None)
        create_kwargs = {
            'fieldset_rule': self.instance,
            'account': self.account,
            'template_id': self.instance.template_id,
        }
        api_name = group_or_data_dict.get('api_name')
        if api_name:
            create_kwargs['api_name'] = api_name
        group_or = FieldSetTemplateRuleGroupOr.objects.create(**create_kwargs)
        if groups_and_data is not None:
            for group_and_data in groups_and_data:
                self._create_group_and(
                    group_or=group_or,
                    group_and_data=group_and_data,
                )
        return group_or

    def _update_group_or(
        self,
        group_or: FieldSetTemplateRuleGroupOr,
        group_or_data: Dict,
    ) -> FieldSetTemplateRuleGroupOr:
        groups_and_data = group_or_data.get('groups_and')
        if groups_and_data is not None:
            self._set_groups_and(
                group_or=group_or,
                groups_and_data=groups_and_data,
            )
        return group_or

    def _set_groups_or(self, groups_or_data: List[Dict]):
        existing_groups_or = {
            group_or.api_name: group_or
            for group_or in self.instance.groups_or.all()
        }
        groups_or_api_names = set()
        for group_or_data in groups_or_data:
            group_or_data_dict = dict(group_or_data)
            api_name = group_or_data_dict.get('api_name')
            if api_name and api_name in existing_groups_or:
                group_or = self._update_group_or(
                    group_or=existing_groups_or[api_name],
                    group_or_data=group_or_data_dict,
                )
            else:
                group_or = self._create_group_or(
                    group_or_data=group_or_data_dict,
                )
            groups_or_api_names.add(group_or.api_name)
        self.instance.groups_or.exclude(
            api_name__in=groups_or_api_names,
        ).delete()

    def create(
        self,
        **kwargs,
    ) -> FieldSetTemplateRuleSet:

        with transaction.atomic():
            self._create_instance(**kwargs)
            self._create_related(**kwargs)
            self._create_actions(**kwargs)
        return self.instance

    def partial_update(self, **update_kwargs) -> FieldSetTemplateRuleSet:
        fields = update_kwargs.pop('fields', None)
        groups_or = update_kwargs.pop('groups_or', None)
        with transaction.atomic():
            result = super().partial_update(
                force_save=True,
                **update_kwargs,
            )
            if fields is not None:
                self._set_fields(fields_api_names=fields)
            if groups_or is not None:
                self._set_groups_or(groups_or_data=groups_or)
            return result
