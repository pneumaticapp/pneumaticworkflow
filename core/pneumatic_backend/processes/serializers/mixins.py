# pylint:disable=not-callable
from django.contrib.auth import get_user_model
from rest_framework import serializers
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0052,
    MSG_PW_0055,
)
from pneumatic_backend.processes.enums import (
    FieldType,
)

UserModel = get_user_model()


class OutputCreateMixin:
    selection_field_values_create_serializer = None

    def custom_validate(self, data):

        """ Method used instead of "validate" method
            for pretty error message format """

        field_type = data.get("type")
        if field_type == FieldType.USER:
            required = data.get("is_required")
            if not required:
                raise serializers.ValidationError({
                    'message': MSG_PW_0052,
                    'name': data.get('name'),
                    'api_name': data.get('api_name'),
                })

        selections = data.get('selections', None)
        if field_type in {
            FieldType.CHECKBOX,
            FieldType.RADIO,
            FieldType.DROPDOWN
        } and selections is None:
            raise serializers.ValidationError({
                'message': MSG_PW_0055,
                'name': data.get('name'),
                'api_name': data.get('api_name'),
            })

        if data.get('type') in [
            FieldType.CHECKBOX,
            FieldType.RADIO,
            FieldType.DROPDOWN
        ] and selections is None:
            raise serializers.ValidationError({
                'message': MSG_PW_0055,
                'name': data.get('name'),
                'api_name': data.get('api_name'),
            })

    def create(self, validated_data):
        self.custom_validate(validated_data)
        selections = validated_data.pop('selections', None)

        instance = super().create(validated_data)

        if selections is not None:
            selections = self.selection_field_values_create_serializer(
                data=selections,
                context={'field_template': instance},
                many=True
            )
            selections.is_valid(raise_exception=True)
            selections.save()
        return instance
