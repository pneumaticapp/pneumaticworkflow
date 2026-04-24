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
        if hasattr(instance, 'selections_values'):
            # Prefetched values
            result = [s.value for s in instance.selections_values]
        else:
            # Called for single fields where prefetch is not needed
            result = list(instance.selections.values_list('value', flat=True))
        if instance.dataset_id:
            dataset = instance.dataset
            if hasattr(dataset, 'dataset_values'):
                # Prefetched values
                result.extend([i.value for i in dataset.dataset_values])
            else:
                # Called for single fields where prefetch is not needed
                dataset_values = dataset.items.values_list('value', flat=True)
                result.extend(list(dataset_values))
        return result


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
