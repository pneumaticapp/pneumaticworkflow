from typing import Dict, List, Optional
from django.contrib.auth import get_user_model
from django.db import transaction

from src.generics.base.service import BaseModelService
from src.processes.enums import LabelPosition, FieldSetLayout
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.models.templates.kickoff import Kickoff
from src.processes.services.exceptions import (
    FieldsetTemplateInUseException,
)
from src.processes.services.templates.field_template import (
    FieldTemplateService,
)
from src.processes.services.templates.fieldsets.fieldset_rule import \
    FieldsetTemplateRuleService

UserModel = get_user_model()


class FieldSetTemplateService(BaseModelService):

    def _create_instance(
        self,
        name: str,
        template_id: int,
        order: int = 0,
        description: str = '',
        label_position: LabelPosition.LITERALS = LabelPosition.TOP,
        layout: FieldSetLayout.LITERALS = FieldSetLayout.VERTICAL,
        kickoff_id: Optional[int] = None,
        task_id: Optional[int] = None,
        **kwargs,
    ):
        self.instance = FieldsetTemplate.objects.create(
            template_id=template_id,
            account=self.account,
            name=name,
            description=description,
            order=order,
            label_position=label_position,
            layout=layout,
            kickoff_id=kickoff_id,
            task_id=task_id,
        )
        return self.instance

    def _create_related(
        self,
        rules: Optional[List[Dict]] = None,
        fields: Optional[List[Dict]] = None,
        **kwargs,
    ):
        if fields:
            self._create_fields(fields_data=fields)
        if rules:
            self.create_rules(rules_data=rules)

    def create(
        self,
        **kwargs,
    ) -> FieldsetTemplate:

        template_id = kwargs['template_id']
        if kwargs.get('task_id') is None:
            # Bind fieldset to the kickoff if task_id is not provided
            kwargs['kickoff_id'] = (
                Kickoff.objects.get(template_id=template_id).id
            )
        super().create(**kwargs)
        return self.instance

    def partial_update(
        self,
        **update_kwargs,
    ) -> FieldsetTemplate:

        rules_data = update_kwargs.pop('rules', None)
        fields_data = update_kwargs.pop('fields', None)
        if 'task_id' in update_kwargs:
            if update_kwargs['task_id'] is None:
                # Unbind fieldset from the task and bind to the kickoff
                template_id = self.instance.template_id
                update_kwargs['kickoff_id'] = (
                    Kickoff.objects.get(template_id=template_id).id
                )
            else:
                # Unbind fieldset from the kickoff and bind to the task
                update_kwargs['kickoff_id'] = None

        with transaction.atomic():
            if update_kwargs:
                self.instance = super().partial_update(
                    force_save=True,
                    **update_kwargs,
                )

            if fields_data is not None:
                self._update_fields(fields_data=fields_data)
            if rules_data is not None:
                self.update_rules(rules_data=rules_data)
            self._validate_rules()
            return self.instance

    def _validate_rules(self):
        for rule in self.instance.rules.all():
            service = FieldsetTemplateRuleService(
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
                instance=rule,
            )
            service._validate()

    def delete(self) -> None:
        if self.instance.kickoff or self.instance.task:
            raise FieldsetTemplateInUseException
        self.instance.delete()

    def create_rules(
        self,
        rules_data: List[Dict],
    ):
        service = FieldsetTemplateRuleService(
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
        )
        for rule_data in rules_data:
            service.create(
                fieldset_id=self.instance.id,
                **rule_data,
            )

    def update_rules(
        self,
        rules_data: List[Dict],
    ):
        """ All dataset items will be updated """

        existing_rules = {rule.id: rule for rule in self.instance.rules.all()}
        rules_ids = set()
        for rule_data in rules_data:
            rule_id = rule_data.pop('id', None)
            if rule_id and rule_id in existing_rules:
                service = FieldsetTemplateRuleService(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                    instance=existing_rules[rule_id],
                )
                service.partial_update(force_save=True, **rule_data)
                rules_ids.add(rule_id)
            else:
                service = FieldsetTemplateRuleService(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                )
                rule = service.create(
                    fieldset_id=self.instance.id,
                    **rule_data,
                )
                rules_ids.add(rule.id)

        self.instance.rules.exclude(id__in=rules_ids).delete()

    def _create_fields(
        self,
        fields_data: List[Dict],
    ):
        for field_data in fields_data:
            service = FieldTemplateService(
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
            )
            service.create(
                fieldset_id=self.instance.id,
                template_id=self.instance.template_id,
                **field_data,
            )

    def _update_fields(
        self,
        fields_data: List[Dict],
    ):
        """ All fieldset fields will be updated """

        existing_fields = {
            field.api_name: field
            for field in self.instance.fields.all()
        }
        fields_api_names = set()
        for field_data in fields_data:
            field_api_name = field_data.pop('api_name', None)
            if field_api_name and field_api_name in existing_fields:
                service = FieldTemplateService(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                    instance=existing_fields[field_api_name],
                )
                service.partial_update(force_save=True, **field_data)
                fields_api_names.add(field_api_name)
            else:
                service = FieldTemplateService(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                )
                field = service.create(
                    fieldset_id=self.instance.id,
                    template_id=self.instance.template_id,
                    **field_data,
                )
                fields_api_names.add(field.api_name)

        self.instance.fields.exclude(api_name__in=fields_api_names).delete()
