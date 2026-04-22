from typing import Dict, List, Optional

from src.processes.models.workflows.fieldset import (
    FieldSet,
    FieldSetRule,
)
from src.processes.models.workflows.fields import (
    FieldSelection,
    TaskField,
)
from src.processes.services.base import (
    BaseUpdateVersionService,
)


class KickoffUpdateVersionService(BaseUpdateVersionService):

    def _update_field(
        self,
        template: dict,
        *,
        fieldset: Optional[FieldSet] = None,
    ):

        # TODO Move to TaskFieldService

        return TaskField.objects.update_or_create(
            kickoff=self.instance,
            api_name=template['api_name'],
            fieldset=fieldset,
            defaults={
                'name': template['name'],
                'description': template['description'],
                'type': template['type'],
                'is_required': template['is_required'],
                'is_hidden': template['is_hidden'],
                'order': template['order'],
                'workflow': self.instance.workflow,
                'account': self.instance.account,
                'dataset_id': template['dataset_id'],
            },
        )

    def _update_field_selections(
        self,
        field: TaskField,
        field_data: Dict,
    ) -> None:

        if field_data.get('selections'):
            selection_ids = set()
            for selection_data in field_data['selections']:
                selection, __ = FieldSelection.objects.update_or_create(
                    field=field,
                    api_name=selection_data['api_name'],
                    defaults={
                        'value': selection_data['value'],
                    },
                )
                selection_ids.add(selection.id)
            field.selections.exclude(id__in=selection_ids).delete()

    def _update_fields(
        self,
        data: List[Dict],
    ):

        # TODO Move to TaskFieldService

        field_ids = []
        for field_data in data:
            field, _ = self._update_field(field_data, fieldset=None)
            field_ids.append(field.id)
            self._update_field_selections(field, field_data)
        self.instance.output.filter(
            fieldset__isnull=True,
        ).exclude(id__in=field_ids).delete()

    def _update_fieldset_rules(
        self,
        fieldset: FieldSet,
        rules_data: Optional[List[Dict]],
    ) -> None:

        rule_ids = []
        rules_data = rules_data or []
        for rule_data in rules_data:
            rule, _ = FieldSetRule.objects.update_or_create(
                fieldset=fieldset,
                api_name=rule_data['api_name'],
                defaults={
                    'account_id': fieldset.account_id,
                    'type': rule_data['type'],
                    'value': rule_data.get('value'),
                },
            )
            rule_ids.append(rule.id)
        fieldset.rules.exclude(id__in=rule_ids).delete()

    def _update_field_rules(
        self,
        field: TaskField,
        field_data: Dict,
        fieldset: FieldSet,
    ) -> None:

        rules = field_data.get('rules', [])
        if rules:
            rules_api_names = [e['api_name'] for e in rules]
            rules = FieldSetRule.objects.filter(
                fieldset=fieldset,
                api_name__in=rules_api_names,
            )
            field.rules.set(rules)
        else:
            field.rules.clear()

    def _update_fieldset_fields(
        self,
        fieldset: FieldSet,
        fields_data: Optional[List[Dict]],
    ) -> None:

        field_ids = []
        fields_data = fields_data or []
        for field_data in fields_data:
            field, _ = self._update_field(field_data, fieldset=fieldset)
            field_ids.append(field.id)
            self._update_field_selections(field, field_data)
            self._update_field_rules(field, field_data, fieldset)
        TaskField.objects.filter(
            kickoff=self.instance,
            fieldset=fieldset,
        ).exclude(id__in=field_ids).delete()

    def _update_fieldsets(self, data: Optional[List]) -> None:

        fs_api_names = set()
        for fs_data in data or []:
            fieldset, _ = FieldSet.objects.update_or_create(
                workflow=self.instance.workflow,
                kickoff=self.instance,
                api_name=fs_data['api_name'],
                defaults={
                    'account_id': self.instance.account_id,
                    'name': fs_data['name'],
                    'description': fs_data['description'],
                    'order': fs_data['order'],
                    'label_position': fs_data['label_position'],
                    'layout': fs_data['layout'],
                },
            )
            self._update_fieldset_rules(
                fieldset=fieldset,
                rules_data=fs_data.get('rules'),
            )
            self._update_fieldset_fields(
                fieldset=fieldset,
                fields_data=fs_data.get('fields'),
            )
            fs_api_names.add(fs_data['api_name'])
        FieldSet.objects.filter(
            kickoff=self.instance,
            is_deleted=False,
        ).exclude(api_name__in=fs_api_names).delete()

    def update_from_version(
        self,
        data: dict,
        version: int,
    ):
        """
            data = {
                'description': str,
                'fields': list,
                'fieldsets': list,
            }
        """

        if data.get('fields'):
            self._update_fields(data=data['fields'])
        if data.get('fieldsets') is not None:
            self._update_fieldsets(data=data['fieldsets'])
