from typing import Dict, List

from django.contrib.auth import get_user_model

from src.generics.base.service import BaseModelService
from src.processes.models.templates.fields import FieldTemplateRuleSet
from src.processes.models.workflows.fields import (
    FieldRuleGroupAnd,
    FieldRuleGroupOr,
    FieldRuleSet,
    TaskField,
)
from src.processes.services.base import BaseUpdateVersionService

UserModel = get_user_model()


class FieldRuleSetService(BaseModelService):

    """ Runtime counterpart of FieldTemplateRuleSetService.
        CRUD operations for FieldRuleSet and its groups. """

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
            and_objects = [
                FieldRuleGroupAnd(
                    account=self.account,
                    workflow_id=self.instance.workflow_id,
                    group_or=group_or,
                    api_name=group_and_template.api_name,
                    field=group_and_template.field,
                    operator=group_and_template.operator,
                    value=group_and_template.value,
                )
                for group_and_template
                in group_or_template.groups_and.all()
            ]
            if and_objects:
                FieldRuleGroupAnd.objects.bulk_create(and_objects)


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
