from django.contrib.auth import get_user_model
from rest_framework import serializers

from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0052,
    MSG_PW_0053,
    MSG_PW_0054,
)
from pneumatic_backend.processes.models import FieldTemplate
from pneumatic_backend.processes.serializers.field_template import (
    SelectionFieldValuesCreateSerializer
)
from pneumatic_backend.processes.serializers.mixins import (
    OutputCreateMixin,
)
from pneumatic_backend.processes.enums import FieldType

UserModel = get_user_model()


class KickoffFieldCreateSerializer(
    OutputCreateMixin,
    serializers.ModelSerializer,
):

    class Meta:
        model = FieldTemplate
        fields = (
            'type',
            'name',
            'description',
            'is_required',
            'kickoff',
            'selections',
            'order',
            'default',
            'api_name',
        )

    type = serializers.ChoiceField(choices=FieldType.CHOICES)
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    is_required = serializers.BooleanField(required=False, allow_null=False)
    kickoff = serializers.IntegerField(required=False, source='kickoff_id')
    selections = SelectionFieldValuesCreateSerializer(
        many=True,
        required=False,
    )
    order = serializers.IntegerField(required=False)
    default = serializers.CharField(required=False, allow_blank=True)
    api_name = serializers.CharField(max_length=200, required=False)
    selection_field_values_create_serializer = (
        SelectionFieldValuesCreateSerializer
    )

    def validate(self, data):
        field_type = data.get("type")
        if field_type == FieldType.USER:
            required = data.get("is_required")
            if not required:
                raise serializers.ValidationError({
                    'message': MSG_PW_0052,
                    'name': data.get('name'),
                    'api_name': data.get('api_name')
                })
            default_value = data.get('default')
            if default_value is not None:
                try:
                    value = int(default_value)
                    UserModel.objects.filter(id=value).exists()
                except ValueError:
                    raise serializers.ValidationError({
                        'message': MSG_PW_0053,
                        'name': data.get('name'),
                        'api_name': data.get('api_name')
                    })
                except UserModel.DoesNotExist:
                    raise serializers.ValidationError({
                        'message': MSG_PW_0054,
                        'name': data.get('name'),
                        'api_name': data.get('api_name')
                    })

        return data
