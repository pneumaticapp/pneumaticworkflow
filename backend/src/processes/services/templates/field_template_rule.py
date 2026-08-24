from typing import Dict, List, Optional

from django.db import transaction

from src.generics.base.service import BaseModelService
from src.processes.enums import FieldRuleOperator
from src.processes.messages.template import MSG_PT_0078
from src.processes.models.templates.fields import (
    FieldTemplateRuleGroupAnd,
    FieldTemplateRuleGroupOr,
    FieldTemplateRuleSet,
)
from src.processes.services.exceptions import \
    FieldTemplateRuleSetServiceException


class FieldTemplateRuleSetService(BaseModelService):

    def _create_instance(
        self,
        field_id: int,
        type: str,  # noqa: A002
        api_name: Optional[str] = None,
        message: Optional[str] = None,
        order: int = 0,
        template_id: Optional[int] = None,
        **kwargs,
    ):

        create_kwargs = {
            'account': self.account,
            'type': type,
            'message': message,
            'order': order,
            'field_id': field_id,
            'template_id': template_id,
        }
        if api_name:
            create_kwargs['api_name'] = api_name
        self.instance = FieldTemplateRuleSet.objects.create(**create_kwargs)
        return self.instance

    def _create_related(
        self,
        **kwargs,
    ):
        groups_or = kwargs.pop('groups_or', None)
        if groups_or is not None:
            self._set_groups_or(groups_or_data=groups_or)

    def _validate(
        self,
        group_and: FieldTemplateRuleGroupAnd,
    ):
        field = self.instance.field
        allowed_operators = FieldRuleOperator.ALLOWED_OPERATORS[field.type]
        if group_and.operator not in allowed_operators:
            raise FieldTemplateRuleSetServiceException(
                message=MSG_PT_0078(
                    field=field,
                    operator=group_and.operator,
                    field_type=field.type,
                ),
            )

    def _create_group_and(
        self,
        group_or: FieldTemplateRuleGroupOr,
        group_and_data: Dict,
    ) -> FieldTemplateRuleGroupAnd:
        create_kwargs = {
            'group_or': group_or,
            'account': self.account,
            'template_id': self.instance.template_id,
            'field': group_and_data.get('field'),
            'operator': group_and_data['operator'],
            'value': group_and_data.get('value'),
        }
        api_name = group_and_data.get('api_name')
        if api_name:
            create_kwargs['api_name'] = api_name
        group_and = FieldTemplateRuleGroupAnd.objects.create(
            **create_kwargs,
        )
        self._validate(group_and=group_and)
        return group_and

    def _update_group_and(
        self,
        group_and: FieldTemplateRuleGroupAnd,
        group_and_data: Dict,
    ) -> FieldTemplateRuleGroupAnd:
        update_fields = []
        if 'field' in group_and_data:
            group_and.field = group_and_data['field']
            update_fields.append('field')
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
        group_or: FieldTemplateRuleGroupOr,
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
    ) -> FieldTemplateRuleGroupOr:
        group_or_data_dict = dict(group_or_data)
        groups_and_data = group_or_data_dict.pop('groups_and', None)
        create_kwargs = {
            'field_rule': self.instance,
            'account': self.account,
            'template_id': self.instance.template_id,
        }
        api_name = group_or_data_dict.get('api_name')
        if api_name:
            create_kwargs['api_name'] = api_name
        group_or = FieldTemplateRuleGroupOr.objects.create(**create_kwargs)
        if groups_and_data is not None:
            for group_and_data in groups_and_data:
                self._create_group_and(
                    group_or=group_or,
                    group_and_data=group_and_data,
                )
        return group_or

    def _update_group_or(
        self,
        group_or: FieldTemplateRuleGroupOr,
        group_or_data: Dict,
    ) -> FieldTemplateRuleGroupOr:
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

    def partial_update(self, **update_kwargs) -> FieldTemplateRuleSet:
        groups_or = update_kwargs.pop('groups_or', None)
        with transaction.atomic():
            result = super().partial_update(
                force_save=True,
                **update_kwargs,
            )
            if groups_or is not None:
                self._set_groups_or(groups_or_data=groups_or)
            return result
