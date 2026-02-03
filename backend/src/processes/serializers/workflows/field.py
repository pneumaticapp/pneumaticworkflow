from django.contrib.auth import get_user_model
from rest_framework import serializers

from src.processes.models.workflows.fields import (
    FieldSelection,
    TaskField,
)

UserModel = get_user_model()


class FieldSelectionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldSelection
        fields = (
            'id',
            'value',
            'is_selected',
            'api_name',
        )


class TaskFieldSerializer(serializers.ModelSerializer):

    class Meta:
        model = TaskField
        fields = (
            'id',
            'order',
            'type',
            'is_required',
            'description',
            'api_name',
            'name',
            'value',
            'markdown_value',
            'clear_value',
            'user_id',
            'group_id',
            'selections',
        )

    selections = FieldSelectionListSerializer(many=True, required=False)


class TaskFieldListSerializer(serializers.ModelSerializer):

    class Meta:
        model = TaskField
        fields = (
            'id',
            'order',
            'task_id',
            'kickoff_id',
            'type',
            'is_required',
            'description',
            'api_name',
            'name',
            'value',
            'markdown_value',
            'clear_value',
            'user_id',
            'group_id',
        )
