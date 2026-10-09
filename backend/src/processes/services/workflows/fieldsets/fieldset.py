from itertools import groupby
from typing import Dict, List, Optional
from django.contrib.auth import get_user_model

from src.generics.base.service import BaseModelService
from src.processes.messages.fieldset import MSG_FS_0007, MSG_FS_0012
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.models.workflows.fieldset import FieldSet
from src.processes.services.exceptions import FieldsetServiceException
from src.processes.services.tasks.fields.field import TaskFieldService
from src.processes.services.workflows.fieldsets.fieldset_rule import (
    FieldSetRuleService,
)
from src.processes.services.workflows.fieldsets.fieldset_ruleset import (
    FieldSetRuleSetService,
)

UserModel = get_user_model()


class FieldSetService(BaseModelService):

    def _create_instance(
        self,
        instance_template: FieldsetTemplate,
        **kwargs,
    ):
        task = kwargs.get('task')
        kickoff = kwargs.get('kickoff')
        if not (task or kickoff):
            raise FieldsetServiceException(
                message=MSG_FS_0007,
            )

        self.instance = FieldSet.objects.create(
            account=self.account,
            workflow=kwargs['workflow'],
            kickoff=kickoff,
            task=task,
            api_name=instance_template.api_name,
            name=instance_template.name,
            title=instance_template.title,
            description=instance_template.description,
            order=instance_template.order,
            label_position=instance_template.label_position,
            layout=instance_template.layout,
        )

    def _create_fields(
        self,
        instance_template: FieldsetTemplate,
        fields_data: Optional[List[Dict]] = None,
        skip_value: bool = False,
        **kwargs,
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
                workflow_id=self.instance.workflow_id,
                fieldset_id=self.instance.id,
                skip_value=skip_value,
                value=fields_data.get(field_template.api_name, ''),
            )

    def _create_rulesets(
        self,
        instance_template: FieldsetTemplate,
        **kwargs,
    ):
        ruleset_templates = [
            r for r in instance_template.rulesets.all()
            if not getattr(r, 'is_deleted', False)
        ]
        for ruleset_template in ruleset_templates:
            service = FieldSetRuleSetService(
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
            )
            service.create(
                instance_template=ruleset_template,
                fieldset=self.instance,
                workflow=self.instance.workflow,
                skip_validation=kwargs.get('skip_value', False),
            )

    def _create_related(self, instance_template: FieldsetTemplate, **kwargs):
        self._create_fields(instance_template, **kwargs)
        self._create_rulesets(instance_template, **kwargs)

    def validate_rules(self) -> bool:
        rulesets = list(self.instance.rulesets.order_by('order', 'id').all())
        if rulesets:
            for ruleset in rulesets:
                service = FieldSetRuleSetService(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                    instance=ruleset,
                )
                service.validate()
        elif hasattr(self.instance, 'rules') and self.instance.rules.exists():
            rules = list(self.instance.rules.order_by('id').all())
            for _, group in groupby(rules, key=lambda r: r.type):
                group_rules = list(group)
                if len(group_rules) == 1:
                    service = FieldSetRuleService(
                        user=self.user,
                        instance=group_rules[0],
                    )
                    service.validate()
                else:
                    ex_counter = 0
                    for rule in group_rules:
                        try:
                            service = FieldSetRuleService(
                                user=self.user,
                                instance=rule,
                            )
                            service.validate()
                        except FieldsetServiceException:
                            ex_counter += 1
                    if len(group_rules) == ex_counter:
                        values = ', '.join(
                            str(rule.value) for rule in group_rules
                        )
                        raise FieldsetServiceException(
                            message=MSG_FS_0012(values),
                        )
        return True
