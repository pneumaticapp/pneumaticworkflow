from typing import Dict, List, Optional

from src.processes.models.workflows.fieldset import FieldSet
from src.processes.models.workflows.fields import (
    FieldSelection,
    TaskField,
)
from src.processes.services.base import (
    BaseUpdateVersionService,
)
from src.processes.services.tasks.mixins import RuleSetVersionMixin


class KickoffUpdateVersionService(
    BaseUpdateVersionService,
    RuleSetVersionMixin,
):

    def _update_field(
        self,
        template: dict,
        *,
        fieldset: Optional[FieldSet] = None,
    ):

        # TODO Move to TaskFieldService

        # Runtime fieldset fields are linked via fieldset only (kickoff=None).
        # Look up by fieldset+api_name so values are preserved on version
        # update.
        if fieldset is not None:
            return TaskField.objects.update_or_create(
                fieldset=fieldset,
                api_name=template['api_name'],
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
                    'kickoff': None,
                },
            )

        return TaskField.objects.update_or_create(
            kickoff=self.instance,
            api_name=template['api_name'],
            fieldset=None,
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
        version: int = 0,
    ):

        # TODO Move to TaskFieldService

        field_ids = []
        for field_data in data:
            field, _ = self._update_field(field_data, fieldset=None)
            field_ids.append(field.id)
            self._update_field_selections(field, field_data)
            self._update_field_rulesets(field, field_data, version)
        self.instance.output.filter(
            fieldset__isnull=True,
        ).exclude(id__in=field_ids).delete()

    def _update_fieldset_fields(
        self,
        fieldset: FieldSet,
        fields_data: Optional[List[Dict]],
        version: int,
    ) -> None:

        field_ids = []
        fields_data = fields_data or []
        for field_data in fields_data:
            field, _ = self._update_field(field_data, fieldset=fieldset)
            field_ids.append(field.id)
            self._update_field_selections(field, field_data)
            self._update_field_rulesets(field, field_data, version)
        TaskField.objects.filter(
            fieldset=fieldset,
        ).exclude(id__in=field_ids).delete()

    def _update_fieldsets(self, data: Optional[List], version: int) -> None:

        fs_api_names = set()
        for fs_data in data or []:
            fieldset, _ = FieldSet.objects.update_or_create(
                workflow=self.instance.workflow,
                kickoff=self.instance,
                api_name=fs_data['api_name'],
                defaults={
                    'account_id': self.instance.account_id,
                    'name': fs_data['name'],
                    'title': fs_data['title'],
                    'description': fs_data['description'],
                    'order': fs_data['order'],
                    'label_position': fs_data['label_position'],
                    'layout': fs_data['layout'],
                },
            )
            # Fields first: the ruleset fields m2m resolves api_names
            self._update_fieldset_fields(
                fieldset=fieldset,
                fields_data=fs_data.get('fields'),
                version=version,
            )
            self._update_fieldset_rulesets(
                fieldset=fieldset,
                version=version,
                rulesets_data=fs_data.get('rulesets'),
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
            self._update_fields(data=data['fields'], version=version)
        if data.get('fieldsets') is not None:
            self._update_fieldsets(data=data['fieldsets'], version=version)
