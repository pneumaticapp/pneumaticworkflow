from rest_framework.serializers import (
    ModelSerializer,
    Serializer,
    IntegerField,
)
from pneumatic_backend.processes.models import Checklist
from pneumatic_backend.processes.api_v2.serializers.workflow\
    .checklist_selection import CheckListSelectionSerializer
from pneumatic_backend.generics.serializers import CustomValidationErrorMixin


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
    Serializer
):

    selection_id = IntegerField(required=True)
