from typing import Dict, List, Optional, Union

from django.contrib.auth import get_user_model

from src.generics.base.service import BaseModelService
from src.processes.services.base import BaseUpdateVersionService
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
