from rest_framework import serializers
from pneumatic_backend.processes.models import (
    FieldTemplateSelection,
)


class FieldValuesCreateSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        instance = FieldTemplateSelection.objects.create(
            field_template=self.context['field_template'],
            **validated_data
        )
        return instance

    class Meta:
        model = FieldTemplateSelection
        fields = (
            'id',
            'value',
            'api_name',
        )


class SelectionFieldValuesCreateSerializer(FieldValuesCreateSerializer):

    value = serializers.CharField(max_length=200, required=True)
