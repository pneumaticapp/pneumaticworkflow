from django.contrib.auth import get_user_model
from rest_framework import serializers

from pneumatic_backend.generics.serializers import DateTimeRangeSerializer
from pneumatic_backend.generics.fields import TimeStampField
from pneumatic_backend.processes.models import (
    Workflow,
    Template,
    KickoffValue,
    TaskField,
    FieldSelection,
    FileAttachment,
    WorkflowEvent,
)
from pneumatic_backend.processes.enums import FieldType
UserModel = get_user_model()


class ReportUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'photo',
        )


class TaskActivityTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = (
            'id',
            'name',
        )


class ActivitySelectionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldSelection
        fields = (
            'id',
            'value',
            'is_selected',
        )


class ActivityFileAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileAttachment
        fields = (
            'id',
            'name',
            'url',
            'thumbnail_url',
            'size',
        )


class ActivityFieldSerializer(serializers.ModelSerializer):

    # TODO replace to TaskFieldListSerializer

    selections = ActivitySelectionListSerializer(many=True)
    attachments = ActivityFileAttachmentSerializer(many=True)

    class Meta:
        model = TaskField
        fields = (
            'type',
            'is_required',
            'name',
            'description',
            'api_name',
            'value',
            'user_id',
            'selections',
            'attachments',
        )

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


class ActivityKickoffValueSerializer(serializers.ModelSerializer):
    output = ActivityFieldSerializer(many=True)

    class Meta:
        model = KickoffValue
        fields = (
            'description',
            'output',
        )


class ActivityWorkflowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Workflow
        fields = (
            'id',
            'name',
            'current_task',
            'tasks_count',
            'template',
            'is_legacy_template',
            'legacy_template_name',
            'status',
            'kickoff',
            'is_external',
        )

    template = TaskActivityTemplateSerializer()
    kickoff = serializers.SerializerMethodField()

    def get_kickoff(self, instance):
        kickoff = instance.kickoff_instance
        return (
            ActivityKickoffValueSerializer(kickoff).data if kickoff else None
        )


class HighlightsFilterSerializer(serializers.Serializer):
    templates = serializers.CharField(required=False)
    users = serializers.CharField(required=False)
    date_before = serializers.DateTimeField(required=False, allow_null=True)
    date_after = serializers.DateTimeField(required=False, allow_null=True)
    date_before_tsp = TimeStampField(required=False, allow_null=True)
    date_after_tsp = TimeStampField(required=False, allow_null=True)

    def validate(self, attrs):
        if attrs.get('date_before_tsp') is not None:
            attrs['date_before'] = attrs['date_before_tsp']
        if attrs.get('date_after_tsp') is not None:
            attrs['date_after'] = attrs['date_after_tsp']
        return attrs


class EventHighlightsSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkflowEvent
        fields = (
            'id',
            'type',
            'task',
            'text',
            'delay',
            'created',
            'created_tsp',
            'user_id',
            'target_user_id',
            'workflow',
        )

    task = serializers.JSONField(source='task_json')
    delay = serializers.JSONField(source='delay_json')
    workflow = ActivityWorkflowSerializer()
    created_tsp = TimeStampField(source='created')


class AccountDashboardOverviewSerializer(serializers.Serializer):
    launched = serializers.IntegerField(read_only=True)
    completed = serializers.IntegerField(read_only=True)
    ongoing = serializers.IntegerField(read_only=True)
    snoozed = serializers.IntegerField(read_only=True)


class DashboardFilterSerializer(DateTimeRangeSerializer):
    now = serializers.BooleanField()


class BreakdownByStepsFilterSerializer(DashboardFilterSerializer):
    template_id = serializers.IntegerField()
