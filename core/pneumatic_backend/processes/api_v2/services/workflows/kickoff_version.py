from typing import Dict, List
from pneumatic_backend.processes.api_v2.services.base import (
    BaseUpdateVersionService,
)
from pneumatic_backend.processes.models import (
    FieldSelection,
    TaskField,
)


class KickoffUpdateVersionService(BaseUpdateVersionService):

    def _update_field(self, template: dict):

        # TODO Move to TaskFieldService

        return TaskField.objects.update_or_create(
            kickoff=self.instance,
            template_id=template['id'],
            defaults={
                'name': template['name'],
                'description': template['description'],
                'type': template['type'],
                'is_required': template['is_required'],
                'api_name': template['api_name'],
                'order': template['order'],
                'workflow': self.instance.workflow
            }
        )

    def _update_fields(
        self,
        data: List[Dict]
    ):

        # TODO Move to TaskFieldService

        field_ids = []
        for field_data in data:
            field, _ = self._update_field(field_data)
            field_ids.append(field.id)
            if field_data.get('selections'):
                selection_ids = set()
                for selection_data in field_data['selections']:
                    selection, __ = FieldSelection.objects.update_or_create(
                        field=field,
                        template_id=selection_data['id'],
                        defaults={
                            'value': selection_data['value'],
                            'api_name': selection_data['api_name'],
                        }
                    )
                    selection_ids.add(selection.id)
                field.selections.exclude(id__in=selection_ids).delete()
        self.instance.output.exclude(id__in=field_ids).delete()

    def update_from_version(
        self,
        data: dict,
        version: int
    ):
        """
            data = {
                'description': str,
                'fields': list
            }
        """

        self.instance.description = data['description']
        self.instance.clear_description = data['clear_description']
        self.instance.save(update_fields=['description', 'clear_description'])
        if data.get('fields'):
            self._update_fields(data=data['fields'])
