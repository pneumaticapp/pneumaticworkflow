from typing import Dict, Any
from rest_framework.serializers import (
    ModelSerializer,
    CharField
)
from pneumatic_backend.processes.models import (
    Kickoff
)
from pneumatic_backend.processes.api_v2.serializers.template.field import (
    PublicFieldTemplateSerializer
)


class PublicKickoffSerializer(ModelSerializer):

    class Meta:
        model = Kickoff
        fields = (
            'description',
            'fields'
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
