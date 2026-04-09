from typing import List, Optional, Dict
from django.contrib.auth import get_user_model
from src.generics.base.service import BaseModelService
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.services.exceptions import (
    FieldsetTemplateInUseException,
)
from src.processes.services.templates.fieldsets.fieldset_rule import \
    FieldsetTemplateRuleService

UserModel = get_user_model()


class FieldsetTemplateService(BaseModelService):

    def _create_instance(
        self,
        name: str,
        description: str = '',
        **kwargs,
    ):
        self.instance = FieldsetTemplate.objects.create(
            account=self.account,
            name=name,
            description=description,
        )
        return self.instance

    def _create_related(
        self,
        rules: Optional[List[Dict]] = None,
        **kwargs,
    ):
        if rules:
            self.create_rules(rules_data=rules)

    def partial_update(
        self,
        **update_kwargs,
    ) -> FieldsetTemplate:

        rules_data = update_kwargs.pop('rules', None)
        result = super().partial_update(
            force_save=True,
            **update_kwargs,
        )

        if rules_data is not None:
            self.update_rules(rules_data=rules_data)

        return result

    def delete(self) -> None:
        if (
            self.instance.kickoff_set.exists()
            or self.instance.tasktemplate_set.exists()
        ):
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
                    dataset_id=self.instance.id,
                    **rule_data,
                )
                rules_ids.add(rule.id)

        self.instance.rules.exclude(id__in=rules_ids).delete()
