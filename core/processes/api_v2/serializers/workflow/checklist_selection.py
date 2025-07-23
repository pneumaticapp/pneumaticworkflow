from rest_framework.serializers import (
    ModelSerializer,
    ReadOnlyField,
)
from pneumatic_backend.processes.models import ChecklistSelection


class CheckListSelectionSerializer(ModelSerializer):

    class Meta:
        model = ChecklistSelection
        fields = (
            'id',
            'api_name',
            'value',
            'is_selected',
        )

    is_selected = ReadOnlyField()
