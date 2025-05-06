from django.contrib.auth import get_user_model
from rest_framework import serializers
from pneumatic_backend.processes.enums import (
    FieldType
)
from pneumatic_backend.processes.models import (
    TaskField,
    FieldSelection,
)
from pneumatic_backend.processes.api_v2.serializers.file_attachment import (
    FileAttachmentSerializer,
)

UserModel = get_user_model()


class FieldSelectionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldSelection
        fields = (
            'id',
            'value',
            'is_selected',
            'api_name'
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
            'user_id',
            'group_id',
            'selections',
            'attachments',
        )

    selections = FieldSelectionListSerializer(many=True, required=False)
    attachments = FileAttachmentSerializer(many=True)
    value = serializers.SerializerMethodField(method_name='get_v')

    # TODO Remove in https://my.pneumatic.app/workflows/40801/
    def get_v(self, instance: TaskField):
        if instance.type == FieldType.USER:
            if instance.user_id:
                return str(instance.user_id)
            else:
                return ''
        else:
            return instance.value


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
