from rest_framework.serializers import (
    ModelSerializer,
    Serializer,
    IntegerField,
)
from src.processes.models import Checklist
from src.processes.serializers.workflows.checklist_selection import (
    CheckListSelectionSerializer,
)
from src.generics.serializers import CustomValidationErrorMixin


class CheckListSerializer(ModelSerializer):

    class Meta:
        model = Checklist
        fields = (
            'id',
            'api_name',
            'selections',
        )

    selections = CheckListSelectionSerializer(many=True)


class CheckListRequestSerializer(
    CustomValidationErrorMixin,
    Serializer,
):

    selection_id = IntegerField(required=True)
