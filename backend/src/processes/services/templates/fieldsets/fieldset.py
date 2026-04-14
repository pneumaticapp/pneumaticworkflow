from typing import List, Optional, Dict
from django.contrib.auth import get_user_model
from django.db import transaction

from src.generics.base.service import BaseModelService
from src.processes.enums import LabelPosition, FieldSetLayout
from src.processes.models.templates.fieldset import FieldsetTemplate
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
        order: int,
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
            order=order,
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
        if rules:
            self.create_rules(rules_data=rules)
        if fields:
            self._create_fields(fields_data=fields)

    def partial_update(
        self,
        **update_kwargs,
    ) -> FieldsetTemplate:

        with transaction.atomic():
            rules_data = update_kwargs.pop('rules', None)
            fields_data = update_kwargs.pop('fields', None)
            result = super().partial_update(
                force_save=True,
                **update_kwargs,
            )

            if rules_data is not None:
                self.update_rules(rules_data=rules_data)
            if fields_data is not None:
                self._update_fields(fields_data=fields_data)
            self._validate_rules()
            return result

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
                **field_data,
            )

    def _update_fields(
        self,
        fields_data: List[Dict],
    ):
        """ All fieldset fields will be updated """

        existing_fields = {
            field.id: field
            for field in self.instance.fields.all()
        }
        fields_ids = set()
        for field_data in fields_data:
            field_id = field_data.pop('id', None)
            if field_id and field_id in existing_fields:
                service = FieldTemplateService(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                    instance=existing_fields[field_id],
                )
                service.partial_update(**field_data)
                fields_ids.add(field_id)
            else:
                service = FieldTemplateService(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                )
                field = service.create(
                    fieldset_id=self.instance.id,
                    **field_data,
                )
                fields_ids.add(field.id)

        self.instance.fields.exclude(id__in=fields_ids).delete()
