from rest_framework import serializers

from src.processes.models.workflows.fieldset import FieldSet
from src.processes.serializers.workflows.field import TaskFieldSerializer


class FieldSetSerializer(serializers.ModelSerializer):

    class Meta:
        model = FieldSet
        fields = (
            'id',
            'api_name',
            'name',
            'description',
            'order',
            'label_position',
            'layout',
            'fields',
        )

    fields = TaskFieldSerializer(many=True)
