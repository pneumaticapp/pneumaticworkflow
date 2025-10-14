from typing import Any, Dict

from rest_framework.serializers import (
    CharField,
    ModelSerializer,
)

from src.processes.models.templates.kickoff import Kickoff
from src.processes.serializers.templates.field import (
    PublicFieldTemplateSerializer,
)


class PublicKickoffSerializer(ModelSerializer):

    class Meta:
        model = Kickoff
        fields = (
            'description',
            'fields',
        )

    description = CharField(allow_blank=True, default='')
    fields = PublicFieldTemplateSerializer(many=True, required=False)

    def to_representation(self, data: Dict[str, Any]):
        data = super().to_representation(data)
        if data.get('description') is None:
            data['description'] = ''
        if data.get('fields') is None:
            data['fields'] = []
        return data
