from typing import Optional

from src.generics.base.service import BaseModelService
from src.processes.models.templates.fields import FieldTemplateSelection


class FieldTemplateSelectionService(BaseModelService):

    def _create_instance(
        self,
        value: str,
        field_template_id: int,
        template_id: Optional[int] = None,
        api_name: Optional[str] = None,
        **kwargs,
    ):
        params = {
            'value': value,
            'field_template_id': field_template_id,
            'template_id': template_id,
        }
        if api_name:
            params['api_name'] = api_name
        self.instance = FieldTemplateSelection.objects.create(**params)
        return self.instance
