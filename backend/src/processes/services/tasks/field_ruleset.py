from typing import Dict, List, Optional, Union

from django.contrib.auth import get_user_model

from src.generics.base.service import BaseModelService
from src.processes.models.templates.fields import (
    FieldTemplateRuleGroupAnd,
    FieldTemplateRuleGroupOr,
    FieldTemplateRuleSet,
)
from src.processes.models.workflows.fields import (
    FieldRuleGroupAnd,
    FieldRuleGroupOr,
    FieldRuleSet,
    TaskField,
)
from src.processes.utils.common import create_api_name

UserModel = get_user_model()


class FieldRuleSetService(BaseModelService):

    def _create_instance(
        self,
        instance_template: Optional[FieldTemplateRuleSet] = None,
        field: Optional[TaskField] = None,
        **kwargs,
    ) -> FieldRuleSet:
        field_id = kwargs.get('field_id') or getattr(field, 'id', None)
        workflow_id = (
            kwargs.get('workflow_id')
            or getattr(kwargs.get('workflow'), 'id', None)
            or getattr(field, 'workflow_id', None)
        )
        account = (
            self.account
            or getattr(field, 'account', None)
            or getattr(kwargs.get('workflow'), 'account', None)
            or kwargs.get('account')
        )
        api_name = kwargs.get('api_name') or getattr(
            instance_template, 'api_name', None,
        )
        create_kwargs = {
            'account': account,
            'workflow_id': workflow_id,
            'field_id': field_id,
            'name': kwargs.get('name') or getattr(
                instance_template, 'name', '',
            ),
            'type': kwargs.get('type') or getattr(
                instance_template, 'type', None,
            ),
            'message': kwargs.get('message', getattr(
                instance_template, 'message', None,
            )),
            'order': kwargs.get('order', getattr(
                instance_template, 'order', 0,
            )),
        }
        if api_name:
            create_kwargs['api_name'] = api_name

        self.instance = FieldRuleSet.objects.create(**create_kwargs)
        return self.instance

    def _build_group_and(
        self,
        group_or: FieldRuleGroupOr,
        data: Union[FieldTemplateRuleGroupAnd, Dict],
    ) -> FieldRuleGroupAnd:
        if isinstance(data, dict):
            api_name = data.get('api_name')
            operator = data['operator']
            value = data.get('value')
            field = data.get('field')
        else:
            api_name = data.api_name
            operator = data.operator
            value = data.value
            field = data.field

        return FieldRuleGroupAnd(
            account=self.instance.account,
            workflow_id=self.instance.workflow_id,
            group_or=group_or,
            operator=operator,
            value=value,
            field=field,
            api_name=api_name or create_api_name(
                FieldRuleGroupAnd.api_name_prefix,
            ),
        )

    def _create_group_or(
        self,
        data: Union[FieldTemplateRuleGroupOr, Dict],
    ) -> FieldRuleGroupOr:
        if isinstance(data, dict):
            api_name = data.get('api_name')
            groups_and_data = data.get('groups_and', [])
        else:
            api_name = data.api_name
            groups_and_data = [
                a for a in data.groups_and.all()
                if not getattr(a, 'is_deleted', False)
            ]

        group_or = FieldRuleGroupOr.objects.create(
            account=self.instance.account,
            workflow_id=self.instance.workflow_id,
            ruleset=self.instance,
            api_name=api_name or create_api_name('field-rule-group-or'),
        )
        and_objects = [
            self._build_group_and(group_or=group_or, data=and_item)
            for and_item in groups_and_data
        ]
        if and_objects:
            FieldRuleGroupAnd.objects.bulk_create(and_objects)
        return group_or

    def _create_related(
        self,
        instance_template: Optional[FieldTemplateRuleSet] = None,
        groups_or: Optional[List] = None,
        **kwargs,
    ):
        if groups_or is None and instance_template:
            groups_or = [
                g for g in instance_template.groups_or.all()
                if not getattr(g, 'is_deleted', False)
            ]

        if groups_or:
            for group_or_item in groups_or:
                self._create_group_or(data=group_or_item)
