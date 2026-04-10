from rest_framework import serializers

from src.processes.models.workflows.fieldset import Fieldset
from src.processes.serializers.workflows.field import TaskFieldSerializer


class FieldSetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Fieldset
        fields = (
            'id',
            'api_name',
            'name',
            'description',
            'fields',
        )

    fields = TaskFieldSerializer(many=True)
