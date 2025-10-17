from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
    Serializer,
)

from src.generics.serializers import CustomValidationErrorMixin
from src.processes.models.workflows.checklist import Checklist
from src.processes.serializers.workflows.checklist_selection import (
    CheckListSelectionSerializer,
)


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
