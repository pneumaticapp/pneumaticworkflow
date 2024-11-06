from django.contrib.auth import get_user_model
from django_filters.constants import EMPTY_VALUES
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
    FileAttachmentShortSerializer
)

UserModel = get_user_model()


class FieldSelectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldSelection
        fields = (
            'field',
            'value',
            'api_name',
            'is_selected',
            'template_id',
        )


class FieldSelectionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldSelection
        fields = (
            'id',
            'value',
            'is_selected',
            'api_name'
        )


class TaskFieldListSerializer(serializers.ModelSerializer):

    class Meta:
        model = TaskField
        fields = (
            'id',
            'type',
            'is_required',
            'name',
            'description',
            'api_name',
            'value',
            'selections',
            'attachments',
            'order',
            'user_id',
        )

    selections = FieldSelectionListSerializer(many=True, required=False)
    attachments = FileAttachmentSerializer(many=True)
    value = serializers.SerializerMethodField(method_name='get_v')

    # TODO Remove in https://my.pneumatic.app/workflows/18137/
    def get_v(self, instance: TaskField):
        if instance.type == FieldType.USER:
            if instance.user_id:
                return str(instance.user_id)
            else:
                return ''
        else:
            return instance.value


class WorkflowTaskFieldListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        fields = self.context['request'].query_params.get('fields')
        if fields not in EMPTY_VALUES:
            fields = fields.replace(' ', '').split(',')
            data = data.filter(api_name__in=fields)
        return super().to_representation(data)


class WorkflowTaskFieldSerializer(serializers.ModelSerializer):
    selections = FieldSelectionListSerializer(many=True, required=False)
    attachments = FileAttachmentShortSerializer(many=True)

    class Meta:
        model = TaskField
        list_serializer_class = WorkflowTaskFieldListSerializer
        fields = (
            'id',
            'task_id',
            'kickoff_id',
            'type',
            'api_name',
            'name',
            'value',
            'selections',
            'attachments',
        )
