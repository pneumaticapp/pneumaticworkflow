from typing import Dict, List

from src.processes.models.workflows.fields import (
    FieldSelection,
    TaskField,
)
from src.processes.services.base import (
    BaseUpdateVersionService,
)


class KickoffUpdateVersionService(BaseUpdateVersionService):

    def _update_field(self, template: dict):

        # TODO Move to TaskFieldService

        return TaskField.objects.update_or_create(
            kickoff=self.instance,
            api_name=template['api_name'],
            defaults={
                'name': template['name'],
                'description': template['description'],
                'type': template['type'],
                'is_required': template['is_required'],
                'order': template['order'],
                'workflow': self.instance.workflow,
            },
        )

    def _update_fields(
        self,
        data: List[Dict],
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
                        api_name=selection_data['api_name'],
                        defaults={
                            'value': selection_data['value'],
                        },
                    )
                    selection_ids.add(selection.id)
                field.selections.exclude(id__in=selection_ids).delete()
        self.instance.output.exclude(id__in=field_ids).delete()

    def update_from_version(
        self,
        data: dict,
        version: int,
    ):
        """
            data = {
                'description': str,
                'fields': list
            }
        """

        if data.get('fields'):
            self._update_fields(data=data['fields'])
