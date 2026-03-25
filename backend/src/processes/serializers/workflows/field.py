from rest_framework import serializers

from src.processes.models.workflows.fields import (
    FieldSelection,
    TaskField,
)
from src.processes.serializers.file_attachment import (
    FileAttachmentSerializer,
)


class FieldSelectionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldSelection
        fields = (
            'id',
            'value',
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
            'is_hidden',
            'description',
            'api_name',
            'name',
            'value',
            'markdown_value',
            'clear_value',
            'user_id',
            'group_id',
            'selections',
            'attachments',
        )

    selections = serializers.SerializerMethodField()
    attachments = FileAttachmentSerializer(many=True)

    def get_selections(self, instance: TaskField) -> list:
        result = [s.value for s in instance.selections_values]
        if instance.dataset_id:
            for i in instance.dataset.dataset_values:
                result.append(i.value)
        return result
        # return [s.value for s in instance.selections.only('value')]


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
            'is_hidden',
            'description',
            'api_name',
            'name',
            'value',
            'markdown_value',
            'clear_value',
            'user_id',
            'group_id',
        )


class TaskFieldEventSerializer(serializers.ModelSerializer):

    # TODO Replace with TaskFileListSerializer after integrating
    #  the file service. The only difference is the "attachments" field
    #  (which will be removed when integrating the file service).

    class Meta:
        model = TaskField
        fields = (
            'id',
            'order',
            'type',
            'is_required',
            'is_hidden',
            'description',
            'api_name',
            'name',
            'value',
            'markdown_value',
            'clear_value',
            'user_id',
            'group_id',
            'attachments',
        )

    attachments = FileAttachmentSerializer(many=True)
