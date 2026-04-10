from typing import List, Optional, Dict
from django.contrib.auth import get_user_model

from src.generics.base.service import BaseModelService
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.models.workflows.fieldset import FieldSet
from src.processes.services.tasks.field import TaskFieldService
from src.processes.services.workflows.fieldsets.fieldset_rule import (
    FieldSetRuleService,
)

UserModel = get_user_model()


class FieldSetService(BaseModelService):

    def _create_instance(
        self,
        instance_template: FieldsetTemplate,
        **kwargs,
    ):
        self.instance = FieldSet.objects.create(
            account=self.account,
            workflow=kwargs['workflow'],
            kickoff=kwargs.get('kickoff'),
            task=kwargs.get('task'),
            api_name=instance_template.api_name,
            name=instance_template.name,
            description=instance_template.description,
        )

    def _create_fields(
        self,
        instance_template: FieldsetTemplate,
        fields_data: Optional[List[Dict]],
        skip_value: bool = False,
    ):
        fields_data = fields_data or {}
        for field_template in instance_template.fields.all():
            field_service = TaskFieldService(
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
            )
            field_service.create(
                instance_template=field_template,
                workflow=self.instance.workflow,
                fieldset=self.instance,
                skip_value=skip_value,
                value=fields_data.get(field_template.api_name, ''),
            )

    def _create_rules(self, instance_template, **kwargs):
        for rule_template in instance_template.rules.filter(is_deleted=False):
            service = FieldSetRuleService(user=self.user)
            service.create(
                instance_template=rule_template,
                fieldset=self.instance,
                skip_validation=kwargs.get('skip_value'),
            )

    def _create_related(self, instance_template, **kwargs):
        self._create_fields(instance_template, **kwargs)
        self._create_rules(instance_template, **kwargs)

    def validate_rules(self):
        for rule in self.instance.rules.all():
            service = FieldSetRuleService(user=self.user, instance=rule)
            service.validate()
