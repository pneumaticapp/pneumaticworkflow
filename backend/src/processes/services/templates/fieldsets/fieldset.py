from typing import Dict, List, Optional
from django.contrib.auth import get_user_model
from django.db import transaction

from src.generics.base.service import BaseModelService
from src.processes.enums import LabelPosition, FieldSetLayout
from src.processes.models.templates.fieldset import FieldsetTemplate, \
    FieldsetTemplateKickoff, FieldsetTemplateTaskTemplate
from src.processes.models.templates.kickoff import Kickoff
from src.processes.models.templates.template import Template
from src.processes.models.templates.task import TaskTemplate
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
        description: str = '',
        label_position: LabelPosition.LITERALS = LabelPosition.TOP,
        layout: FieldSetLayout.LITERALS = FieldSetLayout.VERTICAL,
        **kwargs,
    ):
        self.instance = FieldsetTemplate.objects.create(
            template_id=template_id,
            account=self.account,
            name=name,
            description=description,
            label_position=label_position,
            layout=layout,
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

    def _validate_rules(self):
        for rule in self.instance.rules.all():
            service = FieldsetTemplateRuleService(
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
                instance=rule,
            )
            service._validate()

    def partial_update(
        self,
        **update_kwargs,
    ) -> FieldsetTemplate:

        rules_data = update_kwargs.pop('rules', None)
        fields_data = update_kwargs.pop('fields', None)
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

    def delete(self) -> None:
        if self.instance.kickoffs.exists() or self.instance.tasks.exists():
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
                service.partial_update(**rule_data)
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

    @classmethod
    def create_or_update_kickoff_links(
        cls,
        fieldsets_links: List[dict],
        template: Template,
        kickoff: Optional[Kickoff] = None,
    ):
        api_names = {e['api_name'] for e in fieldsets_links}
        for fieldset_link in fieldsets_links:
            fieldset_template = FieldsetTemplate.objects.get(
                template=template,
                api_name=fieldset_link['api_name'],
            )
            FieldsetTemplateKickoff.objects.update_or_create(
                fieldset=fieldset_template,
                kickoff=kickoff,
                defaults={
                    'order': fieldset_link['order'],
                },
            )
        (
            FieldsetTemplateKickoff.objects
            .filter(kickoff=kickoff)
            .exclude(fieldset__api_name__in=api_names)
            .delete()
        )

    @classmethod
    def create_or_update_tasks_links(
        cls,
        fieldsets_links: List[dict],
        template: Template,
        task: Optional[TaskTemplate] = None,
    ):
        api_names = {e['api_name'] for e in fieldsets_links}
        for fieldset_link in fieldsets_links:
            fieldset_template = FieldsetTemplate.objects.get(
                template=template,
                api_name=fieldset_link['api_name'],
            )
            FieldsetTemplateTaskTemplate.objects.update_or_create(
                fieldset=fieldset_template,
                task=task,
                defaults={
                    'order': fieldset_link['order'],
                },
            )
        (
            FieldsetTemplateTaskTemplate.objects
            .filter(task=task)
            .exclude(fieldset__api_name__in=api_names)
            .delete()
        )
