from typing import Dict, Any, Type

from rest_framework.serializers import Serializer

from src.processes.models.templates.template import (
    TemplateVersion,
    Template,
)

class TemplateVersioningService:
    def __init__(
        self,
        schema: Type[Serializer],
    ):
        self.schema = schema

    def map_to_dict(self, template: Template) -> Dict[str, Any]:
        return self.schema(instance=template).data

    def get_template_dict(
        self,
        template_id: int,
        version: int,
    ) -> Dict[str, Any]:
        return TemplateVersion.objects.get(
            template_id=template_id,
            version=version,
        ).data

    def save(self, template: Template) -> TemplateVersion:
        template_dict = self.map_to_dict(template)
        instance, _ = TemplateVersion.objects.update_or_create(
            template_id=template.id,
            version=template.version,
            defaults={
                "data": template_dict,
            },
        )
        return instance
