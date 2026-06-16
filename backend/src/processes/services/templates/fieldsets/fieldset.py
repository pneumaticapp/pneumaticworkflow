# ruff: noqa: PLC0415
from copy import deepcopy
from typing import Dict, List, Optional
from django.contrib.auth import get_user_model
from django.db import transaction

from src.generics.base.service import BaseModelService
from src.processes.enums import LabelPosition, FieldSetLayout
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldsetTemplateRule,
)
from src.processes.services.exceptions import (
    FieldsetTemplateInUseException,
    FieldsetTemplateInUseException2,
)
from src.processes.services.templates.field_template import (
    FieldTemplateService,
)
from src.processes.services.templates.fieldsets.fieldset_rule import \
    FieldsetTemplateRuleService
from src.processes.utils.common import create_api_name


UserModel = get_user_model()


class FieldSetTemplateService(BaseModelService):

    def _create_instance(
        self,
        name: str,
        template_id: int,
        is_shared: bool,
        order: int = 0,
        title: str = '',
        description: str = '',
        kickoff_id: Optional[int] = None,
        task_id: Optional[int] = None,
        shared_fieldset_id: Optional[int] = None,
        api_name: Optional[str] = None,
        label_position: LabelPosition.LITERALS = LabelPosition.TOP,
        layout: FieldSetLayout.LITERALS = FieldSetLayout.VERTICAL,
        **kwargs,
    ):
        create_kwargs = {
            'template_id': template_id,
            'account': self.account,
            'order': order,
            'name': name,
            'title': title,
            'description': description,
            'label_position': label_position,
            'layout': layout,
            'kickoff_id': kickoff_id,
            'task_id': task_id,
            'shared_fieldset_id': shared_fieldset_id,
            'is_shared': is_shared,
        }
        if api_name:
            create_kwargs['api_name'] = api_name
        self.instance = FieldsetTemplate.objects.create(**create_kwargs)
        return self.instance

    def create_shared_fieldset(
        self,
        name: str,
        title: str = '',
        description: str = '',
        api_name: Optional[str] = None,
        label_position: LabelPosition.LITERALS = LabelPosition.TOP,
        layout: FieldSetLayout.LITERALS = FieldSetLayout.VERTICAL,
        **kwargs,
    ):

        """ Creates a shared FieldSetTemplate
            that is not linked to a template. """

        return super().create(
            name=name,
            title=title,
            description=description,
            api_name=api_name,
            label_position=label_position,
            layout=layout,
            is_shared=True,
            **kwargs,
        )

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
                account=self.account,
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

        if self.instance.is_shared and self.instance.child_fieldsets.exists():
            raise FieldsetTemplateInUseException2

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

    def partial_update_instance(
        self,
        **update_kwargs,
    ) -> FieldsetTemplate:

        with transaction.atomic():
            if update_kwargs:
                self.instance = super().partial_update(
                    force_save=True,
                    **update_kwargs,
                )
            return self.instance

    def delete(self) -> None:
        if self.instance.is_shared and self.instance.child_fieldsets.exists():
            raise FieldsetTemplateInUseException
        if self.instance.kickoff_id or self.instance.task_id:
            raise FieldsetTemplateInUseException
        self.instance.delete()

    def _replace_api_names(self, shared_fieldset_data: dict) -> dict:

        fieldset_data = deepcopy(shared_fieldset_data)
        fieldset_data['api_name'] = create_api_name(
            FieldsetTemplate.api_name_prefix,
        )
        fields_map: Dict[str, str] = {}
        updated_fields_data = []
        for field_data in fieldset_data.get('fields', []):
            new_api_name = create_api_name(
                FieldTemplate.api_name_prefix,
            )
            fields_map[field_data['api_name']] = new_api_name
            field_data['api_name'] = new_api_name
            updated_fields_data.append(field_data)
        fieldset_data['fields'] = updated_fields_data

        updated_rules_data = []
        for rule_data in fieldset_data.get('rules', []):
            rule_data['api_name'] = create_api_name(
                FieldsetTemplateRule.api_name_prefix,
            )
            rule_data['fields'] = [
                fields_map[old_api_name]
                for old_api_name in rule_data.get('fields', [])
            ]
            updated_rules_data.append(rule_data)
        fieldset_data['rules'] = updated_rules_data
        return fieldset_data

    def get_new_fieldset_data(
        self,
        shared_fieldset_data: dict,
        api_name: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:

        fieldset_data = self._replace_api_names(shared_fieldset_data)
        if api_name:
            fieldset_data['api_name'] = api_name
        if title:
            fieldset_data['title'] = title
        if description:
            fieldset_data['description'] = description
        fieldset_data.pop('order', None)
        return fieldset_data

    def create_from_shared(
        self,
        shared_fieldset_data: dict,
        shared_fieldset_id: int,
        template_id: int,
        order: int = 0,
        kickoff_id: Optional[int] = None,
        task_id: Optional[int] = None,
        api_name: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> FieldsetTemplate:

        fieldset_data = self.get_new_fieldset_data(
            shared_fieldset_data=shared_fieldset_data,
            api_name=api_name,
            title=title,
            description=description,
        )

        return self.create(
            **fieldset_data,
            is_shared=True,
            shared_fieldset_id=shared_fieldset_id,
            order=order,
            kickoff_id=kickoff_id,
            task_id=task_id,
            template_id=template_id,
        )

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

    @staticmethod
    def to_json(fieldset: FieldsetTemplate) -> dict:
        if fieldset.is_shared:
            from src.processes.serializers.templates.fieldset import (
                SharedFieldsetTemplateSerializer,
            )
            slz_cls = SharedFieldsetTemplateSerializer
        else:
            from src.processes.serializers.templates.fieldset import (
                FieldsetTemplateSerializer,
            )
            slz_cls = FieldsetTemplateSerializer
        return dict(slz_cls(fieldset).data)
