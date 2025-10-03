from typing import Dict, Any, Optional, List
from django.contrib.auth import get_user_model
from src.generics.base.service import BaseModelService
from src.processes.models.templates.preset import (
    TemplatePreset,
    TemplatePresetField
)
from src.processes.models.templates.template import Template
from src.processes.enums import PresetType


UserModel = get_user_model()


class TemplatePresetService(BaseModelService):
    def _create_instance(
        self,
        template: Template,
        name: str,
        is_default: bool = False,
        preset_type: str = PresetType.PERSONAL,
        **kwargs
    ):
        self.instance = TemplatePreset.objects.create(
            template=template,
            author=self.user,
            account=self.account,
            name=name,
            is_default=is_default,
            type=preset_type
        )
        return self.instance

    def _create_related(
        self,
        fields: Optional[List[Dict[str, Any]]] = None,
        is_default: bool = False,
        **kwargs
    ):
        if is_default:
            self._reset_default_presets()
        if fields:
            self._create_or_update_preset_fields(fields_data=fields)

    def partial_update(
        self,
        force_save: bool = False,
        **update_kwargs
    ) -> TemplatePreset:
        fields = update_kwargs.pop('fields', None)
        is_default = update_kwargs.get('is_default')

        result = super().partial_update(force_save=force_save, **update_kwargs)

        if is_default:
            self._reset_default_presets()

        if fields:
            self._create_or_update_preset_fields(fields_data=fields)

        return result

    def set_default(self) -> TemplatePreset:
        self.partial_update(is_default=True, force_save=True)
        return self.instance

    def delete(self) -> None:
        self.instance.delete()

    def _reset_default_presets(self) -> None:
        queryset = (
            TemplatePreset.objects
            .filter(
                template_id=self.instance.template_id,
                type=self.instance.type,
                is_default=True
            )
            .exclude(id=self.instance.id)
        )
        if self.instance.type == PresetType.PERSONAL:
            queryset = queryset.filter(author=self.instance.author)

        queryset.update(is_default=False)

    def _create_or_update_preset_fields(
        self,
        fields_data: List[Dict[str, Any]]
    ):
        self.instance.fields.all().delete()

        fields_to_create = [
            TemplatePresetField(
                preset=self.instance,
                api_name=field_data['api_name'],
                order=field_data.get('order', 0),
                width=field_data.get('width', 100)
            )
            for field_data in fields_data
        ]
        TemplatePresetField.objects.bulk_create(fields_to_create)
